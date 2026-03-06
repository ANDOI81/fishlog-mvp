import secrets
from typing import List, Dict, Any

from app.db import get_conn, has_column


def list_customers() -> List[Dict[str, Any]]:
    with get_conn() as conn:
        cur = conn.cursor()

        has_created = has_column(conn, "customers", "created_at")
        has_phone = has_column(conn, "customers", "phone")
        has_address = has_column(conn, "customers", "address")

        cols = ["id", "name", "region", "token"]
        if has_created:
            cols.append("created_at")
        if has_phone:
            cols.append("phone")
        if has_address:
            cols.append("address")

        cur.execute(f"SELECT {', '.join(cols)} FROM customers ORDER BY id ASC")
        rows = cur.fetchall()

        out: List[Dict[str, Any]] = []
        for r in rows:
            out.append(
                {
                    "id": r["id"],
                    "name": r["name"],
                    "region": r["region"],
                    "token": r["token"],
                    "created_at": r["created_at"] if has_created else None,
                    "phone": r["phone"] if has_phone else None,
                    "address": r["address"] if has_address else None,
                }
            )
        return out


def create_customer(name: str, region: str, phone: str = "", address: str = "") -> int:
    token = secrets.token_urlsafe(9)
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO customers (name, region, token, created_at, phone, address)
            VALUES (?, ?, ?, CURRENT_TIMESTAMP, ?, ?)
            """,
            (name, region, token, phone, address),
        )
        cur.execute("SELECT id FROM customers WHERE token=?", (token,))
        row = cur.fetchone()
        conn.commit()
        try:
            return int(row["id"])
        except Exception:
            return int(row[0])


def rotate_token(customer_id: int) -> str:
    new_token = secrets.token_urlsafe(9)
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("UPDATE customers SET token=? WHERE id=?", (new_token, customer_id))
        conn.commit()
    return new_token


def delete_customer(customer_id: int) -> None:
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("DELETE FROM customers WHERE id=?", (customer_id,))
        conn.commit()


def get_customer_by_token(token: str):
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT id, name, region, token, phone, address FROM customers WHERE token = ? LIMIT 1",
            (token,),
        )
        row = cur.fetchone()
        if not row:
            return None
        return {
            "id": row["id"],
            "name": row["name"],
            "region": row["region"],
            "token": row["token"],
            "phone": row["phone"],
            "address": row["address"],
        }
