from datetime import date, timedelta

from backend.database import create_tables, get_connection
from backend.excel_service import normalize_item_name


def seed_demo():
    create_tables()

    demo_items = [
        ("DEMO001", "샘플 고무장갑 M", "켤레", 1500, 12, 3),
        ("DEMO002", "샘플 페이퍼타올", "박스", 29000, 3, 4),
        ("DEMO003", "샘플 세정제", "EA", 8000, 5, 5),
    ]

    with get_connection() as conn:
        for code, name, unit, price, initial_stock, lead_time in demo_items:
            conn.execute(
                """
                INSERT OR IGNORE INTO items (
                    item_code, normalized_name, item_name, unit,
                    unit_price, initial_stock, lead_time_days
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (code, normalize_item_name(name), name, unit, price, initial_stock, lead_time),
            )

        # 중복 seed 방지
        existing = conn.execute("SELECT COUNT(*) AS cnt FROM stock_requests").fetchone()["cnt"]
        if existing == 0:
            today = date.today()
            request_pattern = [4, 6, 5, 7, 4, 8]
            for item_index, (code, *_rest) in enumerate(demo_items):
                for index, qty in enumerate(request_pattern):
                    request_date = today - timedelta(days=(30 - index * 5))
                    adjusted_qty = qty + item_index
                    shortage = 2 if index == 2 and item_index == 0 else 0
                    conn.execute(
                        """
                        INSERT INTO stock_requests (
                            item_code, request_date, requested_qty,
                            issued_qty, shortage_qty, department, memo
                        ) VALUES (?, ?, ?, ?, ?, 'DEMO', 'GitHub demo data')
                        """,
                        (
                            code,
                            request_date.isoformat(),
                            adjusted_qty,
                            max(0, adjusted_qty - shortage),
                            shortage,
                        ),
                    )

    print("Demo data seeded.")


if __name__ == "__main__":
    seed_demo()
