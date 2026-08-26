from __future__ import annotations

import csv
import json
from pathlib import Path

from . import db


PRODUCT_FIELDS = [
    "site_id",
    "product_id",
    "title",
    "handle",
    "url",
    "published_at_remote",
    "created_at_remote",
    "updated_at_remote",
    "vendor",
    "product_type",
    "tags_json",
    "price_min",
    "price_max",
    "image",
    "first_seen_at",
    "last_seen_at",
]


def export_products(db_path: str, export_dir: str, site_id: str, fmt: str = "csv") -> Path:
    Path(export_dir).mkdir(parents=True, exist_ok=True)
    with db.db(db_path) as conn:
        rows = db.products_for_export(conn, site_id)
    if fmt == "csv":
        path = Path(export_dir) / f"{site_id}-products.csv"
        with path.open("w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=PRODUCT_FIELDS)
            writer.writeheader()
            for row in rows:
                writer.writerow({field: row[field] for field in PRODUCT_FIELDS})
        return path
    if fmt == "json":
        path = Path(export_dir) / f"{site_id}-products.json"
        data = [{field: row[field] for field in row.keys()} for row in rows]
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        return path
    raise ValueError(f"Unsupported export format: {fmt}")
