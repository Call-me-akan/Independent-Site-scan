from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator

SCHEMA = """
CREATE TABLE IF NOT EXISTS sites (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  base_url TEXT NOT NULL,
  adapter TEXT NOT NULL,
  enabled INTEGER NOT NULL DEFAULT 1,
  interval_minutes INTEGER NOT NULL DEFAULT 15,
  full_scan_pages INTEGER NOT NULL DEFAULT 40,
  incremental_pages INTEGER NOT NULL DEFAULT 1,
  full_scan_cursor_page INTEGER NOT NULL DEFAULT 1,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  baseline_complete INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS products (
  site_id TEXT NOT NULL,
  product_id TEXT NOT NULL,
  handle TEXT,
  title TEXT,
  url TEXT,
  vendor TEXT,
  product_type TEXT,
  tags_json TEXT,
  body_html TEXT,
  created_at_remote TEXT,
  published_at_remote TEXT,
  updated_at_remote TEXT,
  price_min REAL,
  price_max REAL,
  image TEXT,
  raw_json TEXT NOT NULL,
  first_seen_at TEXT NOT NULL,
  last_seen_at TEXT NOT NULL,
  PRIMARY KEY (site_id, product_id)
);

CREATE TABLE IF NOT EXISTS variants (
  site_id TEXT NOT NULL,
  product_id TEXT NOT NULL,
  variant_id TEXT NOT NULL,
  title TEXT,
  sku TEXT,
  price REAL,
  available INTEGER,
  raw_json TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  PRIMARY KEY (site_id, product_id, variant_id)
);

CREATE TABLE IF NOT EXISTS events (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  site_id TEXT NOT NULL,
  event_type TEXT NOT NULL,
  product_id TEXT,
  title TEXT,
  payload_json TEXT NOT NULL,
  notified INTEGER NOT NULL DEFAULT 0,
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS scan_runs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  site_id TEXT NOT NULL,
  scan_type TEXT NOT NULL,
  started_at TEXT NOT NULL,
  finished_at TEXT,
  status TEXT NOT NULL,
  product_count INTEGER NOT NULL DEFAULT 0,
  new_count INTEGER NOT NULL DEFAULT 0,
  error_message TEXT
);
"""


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def connect(db_path: str) -> sqlite3.Connection:
    path = Path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


@contextmanager
def db(db_path: str) -> Iterator[sqlite3.Connection]:
    conn = connect(db_path)
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db(db_path: str) -> None:
    with db(db_path) as conn:
        conn.executescript(SCHEMA)
        migrate(conn)


def migrate(conn: sqlite3.Connection) -> None:
    site_cols = {row["name"] for row in conn.execute("PRAGMA table_info(sites)").fetchall()}
    if "baseline_complete" not in site_cols:
        conn.execute("ALTER TABLE sites ADD COLUMN baseline_complete INTEGER NOT NULL DEFAULT 0")
    if "full_scan_cursor_page" not in site_cols:
        conn.execute("ALTER TABLE sites ADD COLUMN full_scan_cursor_page INTEGER NOT NULL DEFAULT 1")



def upsert_site(conn: sqlite3.Connection, site) -> None:
    ts = now_iso()
    conn.execute(
        """
        INSERT INTO sites (id, name, base_url, adapter, enabled, interval_minutes, full_scan_pages, incremental_pages, full_scan_cursor_page, created_at, updated_at, baseline_complete)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, COALESCE((SELECT baseline_complete FROM sites WHERE id = ?), 0))
        ON CONFLICT(id) DO UPDATE SET
          name=excluded.name,
          base_url=excluded.base_url,
          adapter=excluded.adapter,
          enabled=excluded.enabled,
          interval_minutes=excluded.interval_minutes,
          full_scan_pages=excluded.full_scan_pages,
          incremental_pages=excluded.incremental_pages,
          updated_at=excluded.updated_at
        """,
        (site.id, site.name, site.base_url, site.adapter, int(site.enabled), site.interval_minutes, site.full_scan_pages, site.incremental_pages, 1, ts, ts, site.id),
    )


def existing_product_ids(conn: sqlite3.Connection, site_id: str) -> set[str]:
    rows = conn.execute("SELECT product_id FROM products WHERE site_id = ?", (site_id,)).fetchall()
    return {str(row["product_id"]) for row in rows}


def has_products(conn: sqlite3.Connection, site_id: str) -> bool:
    row = conn.execute("SELECT 1 FROM products WHERE site_id = ? LIMIT 1", (site_id,)).fetchone()
    return row is not None


def baseline_complete(conn: sqlite3.Connection, site_id: str) -> bool:
    row = conn.execute("SELECT baseline_complete FROM sites WHERE id = ?", (site_id,)).fetchone()
    return bool(row and row[0])


def get_scan_cursor(conn: sqlite3.Connection, site_id: str) -> int:
    row = conn.execute("SELECT full_scan_cursor_page FROM sites WHERE id = ?", (site_id,)).fetchone()
    return int(row[0] or 1) if row else 1


def set_scan_cursor(conn: sqlite3.Connection, site_id: str, page: int) -> None:
    conn.execute("UPDATE sites SET full_scan_cursor_page = ?, updated_at = ? WHERE id = ?", (int(page), now_iso(), site_id))


def reset_scan_cursor(conn: sqlite3.Connection, site_id: str) -> None:
    set_scan_cursor(conn, site_id, 1)


def set_baseline_complete(conn: sqlite3.Connection, site_id: str, complete: bool = True) -> None:
    conn.execute("UPDATE sites SET baseline_complete = ?, updated_at = ? WHERE id = ?", (int(complete), now_iso(), site_id))



def mark_interrupted_scans(conn: sqlite3.Connection, site_id: str) -> int:
    cur = conn.execute(
        "UPDATE scan_runs SET status = ?, finished_at = ?, error_message = ? WHERE site_id = ? AND status = ?",
        ("interrupted", now_iso(), "scan interrupted by new run", site_id, "running"),
    )
    return cur.rowcount


def start_scan(conn: sqlite3.Connection, site_id: str, scan_type: str) -> int:
    mark_interrupted_scans(conn, site_id)
    cur = conn.execute(
        "INSERT INTO scan_runs (site_id, scan_type, started_at, status) VALUES (?, ?, ?, ?)",
        (site_id, scan_type, now_iso(), "running"),
    )
    return int(cur.lastrowid)


def finish_scan(conn: sqlite3.Connection, run_id: int, status: str, product_count: int = 0, new_count: int = 0, error_message: str | None = None) -> None:
    conn.execute(
        "UPDATE scan_runs SET finished_at = ?, status = ?, product_count = ?, new_count = ?, error_message = ? WHERE id = ?",
        (now_iso(), status, product_count, new_count, error_message, run_id),
    )


def insert_event(conn: sqlite3.Connection, site_id: str, event_type: str, product_id: str | None, title: str | None, payload: dict, notified: bool = False) -> int:
    cur = conn.execute(
        "INSERT INTO events (site_id, event_type, product_id, title, payload_json, notified, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (site_id, event_type, product_id, title, json.dumps(payload, ensure_ascii=False), int(notified), now_iso()),
    )
    return int(cur.lastrowid)


def set_events_notified(conn: sqlite3.Connection, event_ids: list[int]) -> None:
    if not event_ids:
        return
    placeholders = ",".join("?" for _ in event_ids)
    conn.execute(f"UPDATE events SET notified = 1 WHERE id IN ({placeholders})", event_ids)


def upsert_products(conn: sqlite3.Connection, site_id: str, products: list[dict]) -> list[dict]:
    before = existing_product_ids(conn, site_id)
    ts = now_iso()
    new_products = []
    for product in products:
        product_id = str(product["id"])
        if product_id not in before:
            new_products.append(product)
        conn.execute(
            """
            INSERT INTO products (
              site_id, product_id, handle, title, url, vendor, product_type, tags_json, body_html,
              created_at_remote, published_at_remote, updated_at_remote, price_min, price_max, image,
              raw_json, first_seen_at, last_seen_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(site_id, product_id) DO UPDATE SET
              handle=excluded.handle,
              title=excluded.title,
              url=excluded.url,
              vendor=excluded.vendor,
              product_type=excluded.product_type,
              tags_json=excluded.tags_json,
              body_html=excluded.body_html,
              created_at_remote=excluded.created_at_remote,
              published_at_remote=excluded.published_at_remote,
              updated_at_remote=excluded.updated_at_remote,
              price_min=excluded.price_min,
              price_max=excluded.price_max,
              image=excluded.image,
              raw_json=excluded.raw_json,
              last_seen_at=excluded.last_seen_at
            """,
            (
                site_id, product_id, product.get("handle"), product.get("title"), product.get("url"), product.get("vendor"),
                product.get("product_type"), json.dumps(product.get("tags") or [], ensure_ascii=False), product.get("body_html"),
                product.get("created_at"), product.get("published_at"), product.get("updated_at"), product.get("price_min"), product.get("price_max"),
                product.get("image"), json.dumps(product.get("raw") or product, ensure_ascii=False), ts, ts,
            ),
        )
        for variant in product.get("variants") or []:
            conn.execute(
                """
                INSERT INTO variants (site_id, product_id, variant_id, title, sku, price, available, raw_json, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(site_id, product_id, variant_id) DO UPDATE SET
                  title=excluded.title,
                  sku=excluded.sku,
                  price=excluded.price,
                  available=excluded.available,
                  raw_json=excluded.raw_json,
                  updated_at=excluded.updated_at
                """,
                (
                    site_id, product_id, str(variant.get("id")), variant.get("title"), variant.get("sku"),
                    _float_or_none(variant.get("price")), int(bool(variant.get("available"))) if variant.get("available") is not None else None,
                    json.dumps(variant, ensure_ascii=False), ts,
                ),
            )
    return new_products


def products_for_export(conn: sqlite3.Connection, site_id: str) -> list[sqlite3.Row]:
    return conn.execute(
        "SELECT * FROM products WHERE site_id = ? ORDER BY COALESCE(published_at_remote, created_at_remote, first_seen_at) DESC",
        (site_id,),
    ).fetchall()


def recent_scan_status(conn: sqlite3.Connection) -> list[sqlite3.Row]:
    return conn.execute(
        """
        SELECT s.id, s.name, s.base_url, s.baseline_complete, s.full_scan_cursor_page,
               COUNT(p.product_id) AS product_count,
               sr.started_at, sr.finished_at, sr.status, sr.new_count, sr.error_message
        FROM sites s
        LEFT JOIN products p ON p.site_id = s.id
        LEFT JOIN scan_runs sr ON sr.id = (
          SELECT id FROM scan_runs WHERE site_id = s.id ORDER BY id DESC LIMIT 1
        )
        GROUP BY s.id
        ORDER BY s.id
        """
    ).fetchall()


def _float_or_none(value) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None
