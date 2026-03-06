from __future__ import annotations
from datetime import datetime
from ..db import connect


def list_drivers():
    conn = connect(); cur = conn.cursor()
    cur.execute("SELECT id, username, display_name FROM users WHERE role='driver' ORDER BY id")
    rows = cur.fetchall()
    conn.close()
    return rows


def list_vehicles(active_only: bool = True):
    conn = connect(); cur = conn.cursor()
    if active_only:
        cur.execute("SELECT * FROM vehicles WHERE active=1 ORDER BY id")
    else:
        cur.execute("SELECT * FROM vehicles ORDER BY id")
    rows = cur.fetchall()
    conn.close()
    return rows


def assign_order(order_id: int, driver_user_id: int, vehicle_id: int):
    conn = connect(); cur = conn.cursor()
    cur.execute("SELECT id FROM assignments WHERE order_id=?", (order_id,))
    if cur.fetchone() is None:
        cur.execute(
            "INSERT INTO assignments(order_id, driver_user_id, vehicle_id, assigned_at) VALUES (?,?,?,?)",
            (order_id, driver_user_id, vehicle_id, datetime.now().isoformat(timespec='seconds'))
        )
    else:
        cur.execute(
            "UPDATE assignments SET driver_user_id=?, vehicle_id=?, assigned_at=? WHERE order_id=?",
            (driver_user_id, vehicle_id, datetime.now().isoformat(timespec='seconds'), order_id)
        )
    cur.execute("UPDATE orders SET status='assigned' WHERE id=?", (order_id,))
    conn.commit(); conn.close()


def list_assignments_by_driver(driver_user_id: int, delivery_date: str | None = None):
    conn = connect(); cur = conn.cursor()
    if delivery_date:
        cur.execute(
            """
            SELECT o.*, c.name AS customer_name, c.region AS customer_region,
                   COALESCE(c.address, '') AS customer_address,
                   COALESCE(c.phone, '') AS customer_phone,
                   a.vehicle_id, v.name AS vehicle_name
            FROM assignments a
            JOIN orders o ON a.order_id=o.id
            JOIN customers c ON o.customer_id=c.id
            JOIN vehicles v ON a.vehicle_id=v.id
            WHERE a.driver_user_id=? AND o.delivery_date=?
            ORDER BY o.id DESC
            """,
            (driver_user_id, delivery_date),
        )
    else:
        cur.execute(
            """
            SELECT o.*, c.name AS customer_name, c.region AS customer_region,
                   COALESCE(c.address, '') AS customer_address,
                   COALESCE(c.phone, '') AS customer_phone,
                   a.vehicle_id, v.name AS vehicle_name
            FROM assignments a
            JOIN orders o ON a.order_id=o.id
            JOIN customers c ON o.customer_id=c.id
            JOIN vehicles v ON a.vehicle_id=v.id
            WHERE a.driver_user_id=?
            ORDER BY o.id DESC
            LIMIT 200
            """,
            (driver_user_id,),
        )
    rows = cur.fetchall()
    conn.close()
    return rows


def is_assigned_to_driver(order_id: int, driver_user_id: int) -> bool:
    conn = connect(); cur = conn.cursor()
    cur.execute(
        "SELECT 1 FROM assignments WHERE order_id=? AND driver_user_id=? LIMIT 1",
        (order_id, driver_user_id),
    )
    ok = cur.fetchone() is not None
    conn.close()
    return ok
