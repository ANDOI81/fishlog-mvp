from __future__ import annotations

from typing import Dict, Optional, Tuple
from ..db import get_conn

FISH_TYPES = ["광어", "우럭", "도다리"]
FISH_SIZES = ["소", "중", "대"]


def ensure_defaults_for_date(d: str) -> None:
    conn = get_conn()
    cur = conn.cursor()
    for ft in FISH_TYPES:
        for sz in FISH_SIZES:
            cur.execute(
                """
                INSERT INTO daily_catalog(date, fish_type, fish_size, enabled)
                VALUES (?,?,?,1)
                ON CONFLICT(date, fish_type, fish_size) DO NOTHING
                """,
                (d, ft, sz),
            )
            cur.execute(
                """
                INSERT INTO daily_prices(date, fish_type, fish_size, unit_price)
                VALUES (?,?,?,NULL)
                ON CONFLICT(date, fish_type, fish_size) DO NOTHING
                """,
                (d, ft, sz),
            )
    conn.commit()
    conn.close()


def get_catalog(d: str) -> Dict[Tuple[str, str], bool]:
    ensure_defaults_for_date(d)
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT fish_type, fish_size, enabled FROM daily_catalog WHERE date=?", (d,))
    rows = cur.fetchall()
    conn.close()
    return {(x["fish_type"], x["fish_size"]): bool(x["enabled"]) for x in rows}


def set_catalog(d: str, enabled_map: Dict[Tuple[str, str], bool]) -> None:
    ensure_defaults_for_date(d)
    conn = get_conn()
    cur = conn.cursor()
    for (ft, sz), en in enabled_map.items():
        cur.execute(
            """
            INSERT INTO daily_catalog(date, fish_type, fish_size, enabled)
            VALUES (?,?,?,?)
            ON CONFLICT(date, fish_type, fish_size)
            DO UPDATE SET enabled=excluded.enabled
            """,
            (d, ft, sz, 1 if en else 0),
        )
    conn.commit()
    conn.close()


def get_prices(d: str) -> Dict[Tuple[str, str], Optional[int]]:
    ensure_defaults_for_date(d)
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT fish_type, fish_size, unit_price FROM daily_prices WHERE date=?", (d,))
    rows = cur.fetchall()
    conn.close()
    out: Dict[Tuple[str, str], Optional[int]] = {}
    for x in rows:
        out[(x["fish_type"], x["fish_size"])] = x["unit_price"] if x["unit_price"] is not None else None
    return out


def set_prices(d: str, price_map: Dict[Tuple[str, str], Optional[int]]) -> None:
    ensure_defaults_for_date(d)
    conn = get_conn()
    cur = conn.cursor()
    for (ft, sz), price in price_map.items():
        cur.execute(
            """
            INSERT INTO daily_prices(date, fish_type, fish_size, unit_price)
            VALUES (?,?,?,?)
            ON CONFLICT(date, fish_type, fish_size)
            DO UPDATE SET unit_price=excluded.unit_price
            """,
            (d, ft, sz, price),
        )
    conn.commit()
    conn.close()


def get_unit_price(d: str, fish_type: str, fish_size: str) -> Optional[int]:
    ensure_defaults_for_date(d)
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "SELECT unit_price FROM daily_prices WHERE date=? AND fish_type=? AND fish_size=?",
        (d, fish_type, fish_size),
    )
    row = cur.fetchone()
    conn.close()
    if not row:
        return None
    return row["unit_price"]
