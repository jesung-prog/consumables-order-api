import re

from backend.database import get_connection


def inbound_import_exists(fingerprint: str) -> bool:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT 1 FROM import_history WHERE fingerprint = ?",
            (fingerprint,),
        ).fetchone()
        return row is not None


def _next_auto_code(conn) -> str:
    rows = conn.execute(
        "SELECT item_code FROM items WHERE item_code LIKE 'AUTO%'"
    ).fetchall()

    numbers = []
    for row in rows:
        match = re.fullmatch(r"AUTO(\d+)", row["item_code"])
        if match:
            numbers.append(int(match.group(1)))

    return f"AUTO{(max(numbers, default=0) + 1):04d}"


def preview_inbound_rows(rows: list[dict]) -> dict:
    with get_connection() as conn:
        known = {
            row["normalized_name"]: dict(row)
            for row in conn.execute(
                "SELECT item_code, item_name, normalized_name FROM items WHERE active = 1"
            ).fetchall()
        }

    existing = []
    new_items = []
    seen_new = set()

    for row in rows:
        normalized = row["normalized_name"]
        if normalized in known:
            existing.append(
                {
                    "item_code": known[normalized]["item_code"],
                    "item_name": row["item_name"],
                    "quantity": row["quantity"],
                    "unit_price": row["unit_price"],
                }
            )
        elif normalized not in seen_new:
            new_items.append(
                {
                    "item_name": row["item_name"],
                    "unit": row["unit"],
                    "unit_price": row["unit_price"],
                    "status": "신규자동등록예정",
                }
            )
            seen_new.add(normalized)

    return {
        "total_rows": len(rows),
        "existing_count": len(existing),
        "new_item_count": len(new_items),
        "existing": existing,
        "new_items": new_items,
    }


def save_inbound_rows_auto(
    fingerprint: str,
    file_name: str,
    rows: list[dict],
) -> dict:
    with get_connection() as conn:
        if conn.execute(
            "SELECT 1 FROM import_history WHERE fingerprint = ?",
            (fingerprint,),
        ).fetchone():
            raise ValueError("DUPLICATE_IMPORT")

        known = {
            row["normalized_name"]: dict(row)
            for row in conn.execute(
                "SELECT item_code, normalized_name FROM items"
            ).fetchall()
        }

        saved_count = 0
        new_items = []
        total_quantity = 0.0

        for row in rows:
            normalized = row["normalized_name"]

            if normalized in known:
                item_code = known[normalized]["item_code"]
            else:
                item_code = _next_auto_code(conn)
                conn.execute(
                    """
                    INSERT INTO items (
                        item_code, normalized_name, item_name, unit, unit_price
                    ) VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        item_code,
                        normalized,
                        row["item_name"],
                        row["unit"],
                        row["unit_price"],
                    ),
                )
                known[normalized] = {
                    "item_code": item_code,
                    "normalized_name": normalized,
                }
                new_items.append(
                    {
                        "item_code": item_code,
                        "item_name": row["item_name"],
                        "unit": row["unit"],
                    }
                )

            conn.execute(
                """
                INSERT INTO stock_movements (
                    item_code, movement_type, event_date, quantity,
                    memo, source_file, import_fingerprint, source_row
                ) VALUES (?, 'IN', ?, ?, ?, ?, ?, ?)
                """,
                (
                    item_code,
                    row["event_date"],
                    row["quantity"],
                    row["memo"],
                    file_name,
                    fingerprint,
                    row["source_row"],
                ),
            )

            conn.execute(
                "UPDATE items SET unit_price = ?, unit = ? WHERE item_code = ?",
                (row["unit_price"], row["unit"], item_code),
            )

            saved_count += 1
            total_quantity += float(row["quantity"])

        conn.execute(
            """
            INSERT INTO import_history (
                import_type, fingerprint, file_name, row_count
            ) VALUES ('INBOUND_EXCEL', ?, ?, ?)
            """,
            (fingerprint, file_name, saved_count),
        )

    return {
        "saved_count": saved_count,
        "new_item_count": len(new_items),
        "new_items": new_items,
        "total_quantity": total_quantity,
    }
