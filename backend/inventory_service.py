from datetime import date, datetime, timedelta
import math

from backend.database import get_connection


def _current_stock(conn, item_code: str, initial_stock: float) -> float:
    row = conn.execute(
        """
        SELECT COALESCE(SUM(
            CASE
                WHEN movement_type = 'IN' THEN quantity
                WHEN movement_type = 'OUT' THEN -quantity
                ELSE 0
            END
        ), 0) AS movement_stock
        FROM stock_movements
        WHERE item_code = ?
        """,
        (item_code,),
    ).fetchone()
    return float(initial_stock) + float(row["movement_stock"] or 0)


def get_inventory() -> list[dict]:
    with get_connection() as conn:
        items = conn.execute(
            """
            SELECT item_code, item_name, unit, unit_price, initial_stock
            FROM items
            WHERE active = 1
            ORDER BY item_code
            """
        ).fetchall()

        return [
            {
                "item_code": item["item_code"],
                "item_name": item["item_name"],
                "unit": item["unit"],
                "unit_price": item["unit_price"],
                "current_stock": round(
                    _current_stock(conn, item["item_code"], item["initial_stock"]), 2
                ),
            }
            for item in items
        ]


def get_reorder_analysis(item_code: str) -> dict | None:
    with get_connection() as conn:
        item = conn.execute(
            """
            SELECT item_code, item_name, unit, unit_price,
                   initial_stock, lead_time_days
            FROM items
            WHERE item_code = ? AND active = 1
            """,
            (item_code,),
        ).fetchone()

        if item is None:
            return None

        current_stock = _current_stock(conn, item_code, item["initial_stock"])

        requests = conn.execute(
            """
            SELECT request_date, requested_qty, issued_qty, shortage_qty
            FROM stock_requests
            WHERE item_code = ?
            ORDER BY request_date
            """,
            (item_code,),
        ).fetchall()

        if requests:
            demand_rows = [
                (datetime.fromisoformat(row["request_date"]).date(), float(row["requested_qty"]))
                for row in requests
            ]
            shortage_events = sum(1 for row in requests if float(row["shortage_qty"]) > 0)
            shortage_qty = sum(float(row["shortage_qty"]) for row in requests)
        else:
            outs = conn.execute(
                """
                SELECT event_date, quantity
                FROM stock_movements
                WHERE item_code = ? AND movement_type = 'OUT'
                ORDER BY event_date
                """,
                (item_code,),
            ).fetchall()
            demand_rows = [
                (datetime.fromisoformat(row["event_date"]).date(), float(row["quantity"]))
                for row in outs
            ]
            shortage_events = 0
            shortage_qty = 0.0

        if not demand_rows:
            return {
                "item_code": item["item_code"],
                "item_name": item["item_name"],
                "unit": item["unit"],
                "unit_price": float(item["unit_price"]),
                "current_stock": round(current_stock, 2),
                "avg_daily_demand": 0.0,
                "safety_days": 0,
                "recommended_safety_stock": 0,
                "reorder_point": 0,
                "days_until_reorder": None,
                "predicted_order_date": None,
                "order_now": False,
                "recommended_order_qty_now": 0,
                "estimated_order_qty_at_trigger": 0,
                "reason": "수요 이력이 없어 발주 예측 대상에서 제외됩니다.",
            }

        dates = [row[0] for row in demand_rows]
        total_demand = sum(row[1] for row in demand_rows)
        period_days = max(1, (max(dates) - min(dates)).days + 1)
        avg_daily_demand = total_demand / period_days

        request_count = len(demand_rows)
        if request_count > 1:
            avg_request_interval = max(1.0, (max(dates) - min(dates)).days / (request_count - 1))
        else:
            avg_request_interval = 7.0

        shortage_rate = shortage_events / request_count if request_count else 0.0
        shortage_qty_rate = shortage_qty / total_demand if total_demand else 0.0

        lead_time_days = max(1, int(item["lead_time_days"] or 3))

        # 설명 가능한 MVP 규칙: 기본 2일 + 품절 빈도/수량 가중치
        safety_days = math.ceil(
            2 + (shortage_rate + shortage_qty_rate) * avg_request_interval
        )
        safety_days = min(30, max(2, safety_days))

        safety_stock = math.ceil(avg_daily_demand * safety_days)
        reorder_point = math.ceil(avg_daily_demand * lead_time_days + safety_stock)
        order_cycle_days = max(7, math.ceil(avg_request_interval))
        target_stock = math.ceil(
            avg_daily_demand * (lead_time_days + safety_days + order_cycle_days)
        )

        if current_stock <= reorder_point:
            days_until_reorder = 0
        else:
            days_until_reorder = max(
                0, math.floor((current_stock - reorder_point) / avg_daily_demand)
            )

        predicted_order_date = (date.today() + timedelta(days=days_until_reorder)).isoformat()
        order_now = current_stock <= reorder_point
        recommended_order_qty_now = (
            max(0, math.ceil(target_stock - current_stock)) if order_now else 0
        )
        estimated_order_qty_at_trigger = max(0, math.ceil(target_stock - reorder_point))

        return {
            "item_code": item["item_code"],
            "item_name": item["item_name"],
            "unit": item["unit"],
            "unit_price": float(item["unit_price"]),
            "current_stock": round(current_stock, 2),
            "avg_daily_demand": round(avg_daily_demand, 3),
            "lead_time_days": lead_time_days,
            "safety_days": safety_days,
            "recommended_safety_stock": safety_stock,
            "reorder_point": reorder_point,
            "days_until_reorder": days_until_reorder,
            "predicted_order_date": predicted_order_date,
            "order_now": order_now,
            "recommended_order_qty_now": recommended_order_qty_now,
            "estimated_order_qty_at_trigger": estimated_order_qty_at_trigger,
        }


def get_all_reorder_analysis() -> list[dict]:
    with get_connection() as conn:
        codes = [
            row["item_code"]
            for row in conn.execute(
                "SELECT item_code FROM items WHERE active = 1 ORDER BY item_code"
            ).fetchall()
        ]

    return [result for code in codes if (result := get_reorder_analysis(code)) is not None]
