from __future__ import annotations

import os
import secrets
import sqlite3
from datetime import datetime

from .core.config import settings
from .core.security import hash_password

try:
    import psycopg2
    from psycopg2.extras import DictCursor
except Exception:  # pragma: no cover
    psycopg2 = None
    DictCursor = None


def _normalize_database_url(url: str) -> str:
    if url.startswith("postgres://"):
        return "postgresql://" + url[len("postgres://") :]
    return url


def is_postgres() -> bool:
    return bool(settings.DATABASE_URL)


class PgCursor:
    def __init__(self, cur):
        self._cur = cur

    @staticmethod
    def _adapt_query(query: str) -> str:
        return query.replace("?", "%s")

    def execute(self, query: str, params=None):
        if params is None:
            return self._cur.execute(self._adapt_query(query))
        return self._cur.execute(self._adapt_query(query), params)

    def executemany(self, query: str, seq_of_params):
        return self._cur.executemany(self._adapt_query(query), seq_of_params)

    def fetchone(self):
        return self._cur.fetchone()

    def fetchall(self):
        return self._cur.fetchall()


class PgConnection:
    def __init__(self, dsn: str):
        if psycopg2 is None:
            raise RuntimeError("psycopg2 is required when DATABASE_URL is set")
        self._conn = psycopg2.connect(_normalize_database_url(dsn), cursor_factory=DictCursor)

    def cursor(self) -> PgCursor:
        return PgCursor(self._conn.cursor())

    def commit(self):
        self._conn.commit()

    def rollback(self):
        self._conn.rollback()

    def close(self):
        self._conn.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        if exc_type is None:
            self.commit()
        else:
            self.rollback()
        self.close()


def connect():
    if is_postgres():
        return PgConnection(settings.DATABASE_URL)

    if settings.is_production_like:
        raise RuntimeError("운영 환경에서는 DATABASE_URL이 필수입니다. (SQLite fallback 비활성)")

    db_dir = os.path.dirname(os.path.abspath(settings.DB_PATH))
    if db_dir:
        os.makedirs(db_dir, exist_ok=True)
    conn = sqlite3.connect(settings.DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def get_conn():
    return connect()


def has_column(conn, table: str, column: str) -> bool:
    cur = conn.cursor()
    if is_postgres():
        cur.execute(
            """
            SELECT 1 FROM information_schema.columns
            WHERE table_name=%s AND column_name=%s
            LIMIT 1
            """,
            (table, column),
        )
        return cur.fetchone() is not None

    cur.execute(f"PRAGMA table_info({table})")
    return any(r[1] == column for r in cur.fetchall())


def _ensure_column(conn, table: str, column: str, col_def: str) -> None:
    cur = conn.cursor()
    if is_postgres():
        cur.execute(f"ALTER TABLE {table} ADD COLUMN IF NOT EXISTS {column} {col_def}")
        return

    if not has_column(conn, table, column):
        cur.execute(f"ALTER TABLE {table} ADD COLUMN {column} {col_def}")


SCHEMA_SQLITE = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS users (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  username TEXT UNIQUE NOT NULL,
  password_hash TEXT NOT NULL,
  role TEXT NOT NULL,
  display_name TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS customers (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL,
  region TEXT NOT NULL DEFAULT '',
  token TEXT UNIQUE NOT NULL
);

CREATE TABLE IF NOT EXISTS vehicles (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL,
  active INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS orders (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  customer_id INTEGER NOT NULL,
  fish_type TEXT NOT NULL DEFAULT '광어',
  fish_size TEXT NOT NULL DEFAULT '중',
  qty_kg INTEGER NOT NULL,
  unit_price INTEGER,
  total_price INTEGER,
  discount_amount INTEGER NOT NULL DEFAULT 0,
  net_total INTEGER,
  note TEXT NOT NULL DEFAULT '',
  delivery_date TEXT NOT NULL,
  created_at TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'new',
  FOREIGN KEY(customer_id) REFERENCES customers(id)
);

CREATE TABLE IF NOT EXISTS assignments (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  order_id INTEGER UNIQUE NOT NULL,
  driver_user_id INTEGER NOT NULL,
  vehicle_id INTEGER NOT NULL,
  assigned_at TEXT NOT NULL,
  FOREIGN KEY(order_id) REFERENCES orders(id),
  FOREIGN KEY(driver_user_id) REFERENCES users(id),
  FOREIGN KEY(vehicle_id) REFERENCES vehicles(id)
);

CREATE TABLE IF NOT EXISTS daily_catalog (
  date TEXT NOT NULL,
  fish_type TEXT NOT NULL,
  fish_size TEXT NOT NULL,
  enabled INTEGER NOT NULL DEFAULT 1,
  PRIMARY KEY(date, fish_type, fish_size)
);

CREATE TABLE IF NOT EXISTS daily_prices (
  date TEXT NOT NULL,
  fish_type TEXT NOT NULL,
  fish_size TEXT NOT NULL,
  unit_price INTEGER,
  PRIMARY KEY(date, fish_type, fish_size)
);

CREATE TABLE IF NOT EXISTS payments (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  customer_id INTEGER NOT NULL,
  paid_date TEXT NOT NULL,
  amount INTEGER NOT NULL,
  method TEXT NOT NULL DEFAULT '계좌',
  note TEXT NOT NULL DEFAULT '',
  created_at TEXT NOT NULL,
  FOREIGN KEY(customer_id) REFERENCES customers(id)
);

CREATE INDEX IF NOT EXISTS idx_orders_delivery_date ON orders(delivery_date);
CREATE INDEX IF NOT EXISTS idx_orders_customer_id ON orders(customer_id);
CREATE INDEX IF NOT EXISTS idx_payments_customer_id ON payments(customer_id);
"""

SCHEMA_POSTGRES = [
    """
    CREATE TABLE IF NOT EXISTS users (
      id SERIAL PRIMARY KEY,
      username TEXT UNIQUE NOT NULL,
      password_hash TEXT NOT NULL,
      role TEXT NOT NULL,
      display_name TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS customers (
      id SERIAL PRIMARY KEY,
      name TEXT NOT NULL,
      region TEXT NOT NULL DEFAULT '',
      token TEXT UNIQUE NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS vehicles (
      id SERIAL PRIMARY KEY,
      name TEXT NOT NULL,
      active INTEGER NOT NULL DEFAULT 1
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS orders (
      id SERIAL PRIMARY KEY,
      customer_id INTEGER NOT NULL REFERENCES customers(id),
      fish_type TEXT NOT NULL DEFAULT '광어',
      fish_size TEXT NOT NULL DEFAULT '중',
      qty_kg INTEGER NOT NULL,
      unit_price INTEGER,
      total_price INTEGER,
      discount_amount INTEGER NOT NULL DEFAULT 0,
      net_total INTEGER,
      note TEXT NOT NULL DEFAULT '',
      delivery_date TEXT NOT NULL,
      created_at TEXT NOT NULL,
      status TEXT NOT NULL DEFAULT 'new'
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS assignments (
      id SERIAL PRIMARY KEY,
      order_id INTEGER UNIQUE NOT NULL REFERENCES orders(id),
      driver_user_id INTEGER NOT NULL REFERENCES users(id),
      vehicle_id INTEGER NOT NULL REFERENCES vehicles(id),
      assigned_at TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS daily_catalog (
      date TEXT NOT NULL,
      fish_type TEXT NOT NULL,
      fish_size TEXT NOT NULL,
      enabled INTEGER NOT NULL DEFAULT 1,
      PRIMARY KEY(date, fish_type, fish_size)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS daily_prices (
      date TEXT NOT NULL,
      fish_type TEXT NOT NULL,
      fish_size TEXT NOT NULL,
      unit_price INTEGER,
      PRIMARY KEY(date, fish_type, fish_size)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS payments (
      id SERIAL PRIMARY KEY,
      customer_id INTEGER NOT NULL REFERENCES customers(id),
      paid_date TEXT NOT NULL,
      amount INTEGER NOT NULL,
      method TEXT NOT NULL DEFAULT '계좌',
      note TEXT NOT NULL DEFAULT '',
      created_at TEXT NOT NULL
    )
    """,
    "CREATE INDEX IF NOT EXISTS idx_orders_delivery_date ON orders(delivery_date)",
    "CREATE INDEX IF NOT EXISTS idx_orders_customer_id ON orders(customer_id)",
    "CREATE INDEX IF NOT EXISTS idx_payments_customer_id ON payments(customer_id)",
]


def init_db() -> None:
    conn = connect()
    cur = conn.cursor()

    if is_postgres():
        for stmt in SCHEMA_POSTGRES:
            cur.execute(stmt)
    else:
        cur.executescript(SCHEMA_SQLITE)

    _ensure_column(conn, "customers", "created_at", "TEXT")
    _ensure_column(conn, "customers", "phone", "TEXT")
    _ensure_column(conn, "customers", "address", "TEXT")

    cur.execute("UPDATE customers SET created_at = COALESCE(created_at, CURRENT_TIMESTAMP)")

    cur.execute("SELECT id FROM users WHERE username=?", ("owner",))
    if cur.fetchone() is None:
        cur.execute(
            "INSERT INTO users(username, password_hash, role, display_name) VALUES (?,?,?,?)",
            ("owner", hash_password("owner1234"), "owner", "관리자"),
        )

    for username, display in [("driver1", "기사1"), ("driver2", "기사2")]:
        cur.execute("SELECT id FROM users WHERE username=?", (username,))
        if cur.fetchone() is None:
            cur.execute(
                "INSERT INTO users(username, password_hash, role, display_name) VALUES (?,?,?,?)",
                (username, hash_password("driver1234"), "driver", display),
            )

    cur.execute("SELECT COUNT(*) AS n FROM vehicles")
    v_row = cur.fetchone()
    v_n = v_row["n"] if v_row is not None else 0
    if v_n == 0:
        cur.executemany(
            "INSERT INTO vehicles(name, active) VALUES(?,1)",
            [("1호차(6톤)",), ("2호차(6톤)",)],
        )

    cur.execute("SELECT COUNT(*) AS n FROM customers")
    c_row = cur.fetchone()
    c_n = c_row["n"] if c_row is not None else 0
    if c_n == 0:
        def tok() -> str:
            return secrets.token_urlsafe(10)

        cur.executemany(
            "INSERT INTO customers(name, region, token, phone, address) VALUES (?,?,?,?,?)",
            [
                ("샘플거래처-자갈치", "자갈치", tok(), "", ""),
                ("샘플거래처-미락", "미락", tok(), "", ""),
                ("샘플거래처-인산", "인산", tok(), "", ""),
            ],
        )

    conn.commit()
    conn.close()


def now_ts() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

