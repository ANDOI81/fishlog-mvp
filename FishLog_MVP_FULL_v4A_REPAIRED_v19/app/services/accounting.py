from __future__ import annotations

from datetime import datetime
from typing import Dict, List, Optional, Tuple

from ..db import get_conn

PAY_METHODS = ["계좌", "현금", "카드", "기타"]

def add_payment(customer_id: int, paid_date: str, amount: int, method: str, note: str = "") -> None:
    if method not in PAY_METHODS:
        method = "계좌"
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO payments(customer_id, paid_date, amount, method, note, created_at) VALUES (?,?,?,?,?,?)",
        (
            customer_id,
            paid_date,
            int(amount),
            method,
            note or "",
            datetime.now().isoformat(timespec="seconds"),
        ),
    )
    conn.commit()
    conn.close()

def list_payments(customer_id: int, month: str | None = None):
    conn = get_conn()
    cur = conn.cursor()
    if month:
        cur.execute(
            "SELECT * FROM payments WHERE customer_id=? AND paid_date LIKE ? ORDER BY paid_date DESC, id DESC",
            (customer_id, f"{month}-%"),
        )
    else:
        cur.execute(
            "SELECT * FROM payments WHERE customer_id=? ORDER BY paid_date DESC, id DESC",
            (customer_id,),
        )
    rows = cur.fetchall()
    conn.close()
    return rows

def delete_payment(payment_id: int) -> None:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM payments WHERE id=?", (payment_id,))
    conn.commit()
    conn.close()

def update_order_discount(order_id: int, discount_amount: int) -> None:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT total_price FROM orders WHERE id=?", (order_id,))
    row = cur.fetchone()
    total = row["total_price"] if row else None
    net_total = None if total is None else int(total) - int(discount_amount)
    cur.execute(
        "UPDATE orders SET discount_amount=?, net_total=? WHERE id=?",
        (int(discount_amount), net_total, int(order_id)),
    )
    conn.commit()
    conn.close()

def month_settlement(month: str) -> Dict:
    """month: YYYY-MM"""
    conn = get_conn()
    cur = conn.cursor()

    # orders in month
    cur.execute(
        """SELECT c.id as customer_id, c.name as customer_name, c.region as customer_region,
                  COUNT(o.id) as order_count,
                  SUM(o.qty_kg) as total_kg,
                  SUM(CASE WHEN o.total_price IS NULL THEN 0 ELSE o.total_price END) as gross_sum,
                  SUM(CASE WHEN o.total_price IS NULL THEN 0 ELSE o.discount_amount END) as discount_sum,
                  SUM(CASE WHEN o.net_total IS NULL THEN 0 ELSE o.net_total END) as net_sum,
                  SUM(CASE WHEN o.total_price IS NULL THEN 1 ELSE 0 END) as unknown_price_count
           FROM customers c
           LEFT JOIN orders o
             ON o.customer_id=c.id AND o.delivery_date LIKE ?
           GROUP BY c.id
           ORDER BY c.name ASC""",
        (f"{month}-%",),
    )
    rows = cur.fetchall()

    # payments in month
    cur.execute(
        """SELECT customer_id,
                  SUM(amount) as paid_sum
           FROM payments
           WHERE paid_date LIKE ?
           GROUP BY customer_id""",
        (f"{month}-%",),
    )
    paid_map = {x["customer_id"]: (x["paid_sum"] or 0) for x in cur.fetchall()}

    # overall balance as-of-now (all time): sales - discount - payments
    cur.execute(
        """SELECT c.id as customer_id,
                  SUM(CASE WHEN o.total_price IS NULL THEN 0 ELSE o.total_price END) as all_gross,
                  SUM(CASE WHEN o.total_price IS NULL THEN 0 ELSE o.discount_amount END) as all_discount,
                  (SELECT COALESCE(SUM(p.amount),0) FROM payments p WHERE p.customer_id=c.id) as all_paid
           FROM customers c
           LEFT JOIN orders o ON o.customer_id=c.id
           GROUP BY c.id"""
    )
    bal_rows = cur.fetchall()
    balance_map = {}
    for b in bal_rows:
        all_gross = b["all_gross"] or 0
        all_discount = b["all_discount"] or 0
        all_paid = b["all_paid"] or 0
        balance_map[b["customer_id"]] = int(all_gross) - int(all_discount) - int(all_paid)

    # totals for month (overall)
    total_orders = 0
    total_kg = 0
    gross_total = 0
    discount_total = 0
    net_total = 0
    unknown_total = 0
    for r in rows:
        total_orders += int(r["order_count"] or 0)
        total_kg += int(r["total_kg"] or 0)
        gross_total += int(r["gross_sum"] or 0)
        discount_total += int(r["discount_sum"] or 0)
        net_total += int(r["net_sum"] or 0)
        unknown_total += int(r["unknown_price_count"] or 0)

    paid_total = sum(int(v or 0) for v in paid_map.values())

    conn.close()

    enriched = []
    for r in rows:
        cid = r["customer_id"]
        gross = int(r["gross_sum"] or 0)
        disc = int(r["discount_sum"] or 0)
        net = int(r["net_sum"] or 0)
        paid = int(paid_map.get(cid, 0) or 0)
        balance = int(balance_map.get(cid, 0) or 0)
        enriched.append(
            {
                "customer_id": cid,
                "customer_name": r["customer_name"],
                "customer_region": r["customer_region"],
                "order_count": int(r["order_count"] or 0),
                "total_kg": int(r["total_kg"] or 0),
                "gross_sum": gross,
                "discount_sum": disc,
                "net_sum": net,
                "paid_sum": paid,
                "unknown_price_count": int(r["unknown_price_count"] or 0),
                "balance": balance,
            }
        )

    return {
        "month": month,
        "totals": {
            "order_count": total_orders,
            "total_kg": total_kg,
            "gross_sum": gross_total,
            "discount_sum": discount_total,
            "net_sum": net_total,
            "paid_sum": paid_total,
            "unknown_price_count": unknown_total,
        },
        "rows": enriched,
    }
