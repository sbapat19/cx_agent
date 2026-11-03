"""Database layer. SQLite by default for local testing; set DATABASE_URL to a Postgres URL to use Postgres.

Customers, orders, support cases and return requests are FICTIONAL demo data and simulated transactions.
"""
import json
import os
from contextlib import contextmanager

from sqlalchemy import create_engine, text

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./armani_demo.db")
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+psycopg://", 1)
elif DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+psycopg://", 1)

_engine = None


def engine():
    global _engine
    if _engine is None:
        kwargs = {"connect_args": {"check_same_thread": False}} if DATABASE_URL.startswith("sqlite") else {}
        _engine = create_engine(DATABASE_URL, future=True, **kwargs)
    return _engine


def reset_engine(url: str | None = None):
    """Used by tests to point at a fresh database."""
    global _engine, DATABASE_URL
    if url:
        DATABASE_URL = url
    _engine = None


SCHEMA = [
    # --- verified catalog (source_url + last_verified on every row) ---
    """CREATE TABLE IF NOT EXISTS products (id TEXT PRIMARY KEY, category TEXT, name TEXT, status TEXT,
        source_url TEXT, last_verified TEXT, data TEXT)""",
    """CREATE TABLE IF NOT EXISTS fragrances (id TEXT PRIMARY KEY, name TEXT, status TEXT,
        source_url TEXT, last_verified TEXT, data TEXT)""",
    """CREATE TABLE IF NOT EXISTS gift_sets (id TEXT PRIMARY KEY, name TEXT, price_usd REAL, category TEXT,
        description TEXT, includes TEXT, source_url TEXT, last_verified TEXT, status TEXT)""",
    """CREATE TABLE IF NOT EXISTS policies (topic TEXT PRIMARY KEY, title TEXT, text TEXT, source_url TEXT,
        last_verified TEXT, status TEXT)""",
    """CREATE TABLE IF NOT EXISTS counters (id TEXT PRIMARY KEY, name TEXT, address TEXT, phone TEXT, kind TEXT,
        area TEXT, source_url TEXT, last_verified TEXT)""",
    # --- FICTIONAL demo data and simulated transactions ---
    """CREATE TABLE IF NOT EXISTS customers (id TEXT PRIMARY KEY, name TEXT, email TEXT, blurb TEXT)""",
    """CREATE TABLE IF NOT EXISTS orders (id TEXT PRIMARY KEY, customer_id TEXT, placed_at TEXT, delivered_at TEXT,
        status TEXT, tracking TEXT, shipping_paid REAL, note TEXT, items TEXT)""",
    """CREATE TABLE IF NOT EXISTS support_cases (id TEXT PRIMARY KEY, customer_id TEXT, order_id TEXT,
        issue_type TEXT, summary TEXT, status TEXT, created_at TEXT, context TEXT)""",
    """CREATE TABLE IF NOT EXISTS return_requests (id TEXT PRIMARY KEY, customer_id TEXT, order_id TEXT,
        item_ids TEXT, reason TEXT, status TEXT, created_at TEXT, refund_note TEXT)""",
    """CREATE TABLE IF NOT EXISTS saved_preferences (customer_id TEXT PRIMARY KEY, data TEXT, updated_at TEXT)""",
    """CREATE TABLE IF NOT EXISTS sessions (id TEXT PRIMARY KEY, customer_id TEXT, created_at TEXT)""",
    """CREATE TABLE IF NOT EXISTS messages (id INTEGER PRIMARY KEY AUTOINCREMENT, session_id TEXT, role TEXT,
        content TEXT, trace TEXT, created_at TEXT)""",
]


def init_db():
    with engine().begin() as c:
        for stmt in SCHEMA:
            if not DATABASE_URL.startswith("sqlite"):
                stmt = stmt.replace("INTEGER PRIMARY KEY AUTOINCREMENT", "SERIAL PRIMARY KEY")
            c.execute(text(stmt))


@contextmanager
def conn():
    with engine().begin() as c:
        yield c


def rows(sql: str, **params):
    with conn() as c:
        res = c.execute(text(sql), params)
        return [dict(r._mapping) for r in res]


def one(sql: str, **params):
    r = rows(sql, **params)
    return r[0] if r else None


def execute(sql: str, **params):
    with conn() as c:
        c.execute(text(sql), params)


def j(v):
    return json.dumps(v, ensure_ascii=False)


def jl(s):
    return json.loads(s) if s else None
