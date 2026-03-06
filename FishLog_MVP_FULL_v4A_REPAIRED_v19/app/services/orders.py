import json
from datetime import datetime
from typing import Optional, List, Dict, Any

from app.db import connect
from app.services.pricing import get_unit_price


def _now_local_iso() -> str:
    # Keep as text for SQLite; localtime handled by DB default but we set explicitly too
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def create_order(
    customer_id: int,
    fish_type: str,
    fish_size: str,
    qty_kg: float,
    note: str = "",
    delivery_date: Optional[str] = None,
) -> int:
    """Create an order and return new order id."""
    if qty_kg is None:
        raise ValueError("qty_kg is required")

    qty_kg = float(qty_kg)
    if qty_kg <= 0:
        raise ValueError("qty_kg must be > 0")

    unit_price = get_unit_price(delivery_date, fish_type, fish_size)  # may be None
    if unit_price is None:
        unit_price = 0

    total_price = int(round(qty_kg * float(unit_price)))

    conn = connect()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO orders (
                customer_id,
                fish_type,
                fish_size,
                qty_kg,
                unit_price,
                total_price,
                note,
                delivery_date,
                status,
                created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                customer_id,
                fish_type,
                fish_size,
                qty_kg,
                unit_price,
                total_price,
                note or "",
                delivery_date,
                "new",
                _now_local_iso(),
            ),
        )
        conn.commit()
        return int(cur.lastrowid)
    finally:
        conn.close()


def list_orders(date_str: str, customer_id: Optional[int] = None) -> List[Dict[str, Any]]:
    """List orders for a given delivery_date (YYYY-MM-DD)."""
    conn = connect()
    try:
        cur = conn.cursor()
        if customer_id is None:
            cur.execute(
                """
                SELECT o.id, o.customer_id,
                       c.name  AS customer_name,
                       c.region AS customer_region,
                       o.fish_type, o.fish_size, o.qty_kg, o.unit_price, o.total_price,
                       o.note, o.delivery_date, o.status,
                       a.driver_user_id, u.display_name AS driver_name,
                       a.vehicle_id, v.name AS vehicle_name,
                       o.created_at
                FROM orders o
                LEFT JOIN customers c ON c.id = o.customer_id
                LEFT JOIN assignments a ON a.order_id = o.id
                LEFT JOIN users u ON u.id = a.driver_user_id
                LEFT JOIN vehicles v ON v.id = a.vehicle_id
                WHERE o.delivery_date = ?
                ORDER BY o.id DESC
                """,
                (date_str,),
            )
        else:
            cur.execute(
                """
                SELECT o.id, o.customer_id,
                       c.name  AS customer_name,
                       c.region AS customer_region,
                       o.fish_type, o.fish_size, o.qty_kg, o.unit_price, o.total_price,
                       o.note, o.delivery_date, o.status,
                       a.driver_user_id, u.display_name AS driver_name,
                       a.vehicle_id, v.name AS vehicle_name,
                       o.created_at
                FROM orders o
                LEFT JOIN customers c ON c.id = o.customer_id
                LEFT JOIN assignments a ON a.order_id = o.id
                LEFT JOIN users u ON u.id = a.driver_user_id
                LEFT JOIN vehicles v ON v.id = a.vehicle_id
                WHERE o.delivery_date = ? AND o.customer_id = ?
                ORDER BY o.id DESC
                """,
                (date_str, customer_id),
            )

        rows = cur.fetchall() or []
        out = []
        for r in rows:
            out.append(
                {
                    "id": r[0],
                    "customer_id": r[1],
                    "customer_name": r[2],
                    "customer_region": r[3],
                    "fish_type": r[4],
                    "fish_size": r[5],
                    "qty_kg": r[6],
                    "unit_price": r[7],
                    "total_price": r[8],
                    "note": r[9],
                    "delivery_date": r[10],
                    "status": r[11],
                    "driver_user_id": r[12],
                    "driver_name": r[13],
                    "vehicle_id": r[14],
                    "vehicle_name": r[15],
                    "created_at": r[16],
                }
            )
        return out
    finally:
        conn.close()


def get_order(order_id: int) -> Optional[Dict[str, Any]]:
    conn = connect()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT o.id, o.customer_id,
                       c.name  AS customer_name,
                       c.region AS customer_region,
                       o.fish_type, o.fish_size, o.qty_kg, o.unit_price, o.total_price,
                       o.note, o.delivery_date, o.status,
                       a.driver_user_id, u.display_name AS driver_name,
                       a.vehicle_id, v.name AS vehicle_name,
                       o.created_at
                FROM orders o
                LEFT JOIN customers c ON c.id = o.customer_id
                LEFT JOIN assignments a ON a.order_id = o.id
                LEFT JOIN users u ON u.id = a.driver_user_id
                LEFT JOIN vehicles v ON v.id = a.vehicle_id
            WHERE o.id = ?
            """,
            (order_id,),
        )
        r = cur.fetchone()
        if not r:
            return None
        return {
            "id": r[0],
            "customer_id": r[1],
            "customer_name": r[2],
            "customer_region": r[3],
            "fish_type": r[4],
            "fish_size": r[5],
            "qty_kg": r[6],
            "unit_price": r[7],
            "total_price": r[8],
            "note": r[9],
            "delivery_date": r[10],
            "status": r[11],
                    "driver_user_id": r[12],
                    "driver_name": r[13],
                    "vehicle_id": r[14],
                    "vehicle_name": r[15],
                    "created_at": r[16],
        }
    finally:
        conn.close()


def set_status(order_id: int, status: str) -> None:
    conn = connect()
    try:
        cur = conn.cursor()
        cur.execute("UPDATE orders SET status = ? WHERE id = ?", (status, order_id))
        conn.commit()
    finally:
        conn.close()
