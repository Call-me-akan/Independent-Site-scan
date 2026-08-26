from __future__ import annotations

import html
import json
import re
import time
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Iterable

from .base import AdapterError, FetchResult, float_or_none


@dataclass
class PageSource:
    base_url: str
    source_url: str
    timeout: int = 20


class EmbeddedPageProductsAdapter:
    name = "embedded_page_products"

    def __init__(self, base_url: str, source_url: str = "", timeout: int = 20):
        self.base_url = base_url.rstrip("/")
        self.source_url = source_url or self.base_url
        self.timeout = timeout

    def iter_product_pages(self, max_pages: int = 1, start_page: int = 1):
        seen: set[str] = set()
        for page in range(start_page, start_page + max_pages):
            page_url = set_page_param(self.source_url, page)
            try:
                source = self._get_text(page_url)
            except AdapterError:
                if page == start_page:
                    raise
                break
            raws = extract_products_from_html(source)
            if not raws:
                break
            normalized = []
            for raw in raws:
                product = normalize_embedded_product(self.base_url, raw)
                product_id = str(product.get("id") or product.get("handle"))
                if product_id and product_id not in seen:
                    seen.add(product_id)
                    normalized.append(product)
            if not normalized:
                break
            yield page, normalized
            time.sleep(0.2)

    def fetch_products(self, max_pages: int = 1) -> FetchResult:
        all_products: list[dict] = []
        pages = 0
        for page, products in self.iter_product_pages(max_pages=max_pages):
            all_products.extend(products)
            pages = page
        return FetchResult(products=all_products, pages=pages)

    def _get_text(self, url: str) -> str:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 StoreMonitorAgent/0.1", "Accept": "text/html,*/*"})
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                data = resp.read()
        except Exception as exc:
            raise AdapterError(f"Request failed: {url}: {exc}") from exc
        text = data.decode("utf-8", errors="replace")
        low = text[:500].lower()
        if "just a moment" in low or "verifying your connection" in low:
            raise AdapterError(f"Unexpected challenge page: {url}")
        return text


def set_page_param(url: str, page: int) -> str:
    parsed = urllib.parse.urlparse(url)
    query = urllib.parse.parse_qsl(parsed.query, keep_blank_values=True)
    found = False
    updated = []
    for key, value in query:
        if key == "page":
            updated.append((key, str(page)))
            found = True
        else:
            updated.append((key, value))
    if not found:
        updated.append(("page", str(page)))
    return urllib.parse.urlunparse(parsed._replace(query=urllib.parse.urlencode(updated)))


def extract_products_from_html(source: str) -> list[dict]:
    products: list[dict] = []
    for match in re.finditer(r'<script[^>]+type=["\']shop/json["\'][^>]*>(.*?)</script>', source, re.I | re.S):
        data = _loads_html_json(match.group(1))
        products.extend(_walk_for_products(data))
    for match in re.finditer(r'payload:\s*(\{.*?\})\s*[,}]\s*\n\s*}', source, re.S):
        data = _loads_html_json(match.group(1))
        products.extend(_walk_for_products(data))
    return dedupe_raw_products(products)


def _loads_html_json(raw: str):
    text = html.unescape(raw).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return None


def _walk_for_products(value) -> list[dict]:
    found: list[dict] = []
    if isinstance(value, dict):
        if _looks_like_product(value):
            found.append(value)
        for child in value.values():
            found.extend(_walk_for_products(child))
    elif isinstance(value, list):
        if value and all(isinstance(item, dict) and _looks_like_product(item) for item in value[: min(3, len(value))]):
            found.extend(value)
        else:
            for child in value:
                found.extend(_walk_for_products(child))
    return found


def _looks_like_product(value: dict) -> bool:
    return bool((value.get("slug") or value.get("post_name")) and (value.get("ID") or value.get("id")) and (value.get("title") or value.get("post_title")))


def dedupe_raw_products(products: Iterable[dict]) -> list[dict]:
    seen: set[str] = set()
    result = []
    for product in products:
        key = str(product.get("ID") or product.get("id") or product.get("slug") or product.get("post_name"))
        if key and key not in seen:
            seen.add(key)
            result.append(product)
    return result


def normalize_embedded_product(base_url: str, raw: dict) -> dict:
    handle = raw.get("slug") or raw.get("post_name") or ""
    variants = raw.get("variants") or []
    prices = [float_or_none(v.get("price") or v.get("sale_price")) for v in variants]
    prices.extend([float_or_none(raw.get("min_price")), float_or_none(raw.get("max_price")), float_or_none(raw.get("price"))])
    prices = [p for p in prices if p is not None]
    gallery = raw.get("gallery") or []
    image = ""
    if raw.get("feature_image") and isinstance(raw["feature_image"], dict):
        image = raw["feature_image"].get("url") or raw["feature_image"].get("thumbnail") or ""
    if not image and gallery:
        image = gallery[0].get("url") or gallery[0].get("thumbnail") or ""
    return {
        "id": str(raw.get("ID") or raw.get("id") or handle),
        "title": raw.get("title") or raw.get("post_title") or "",
        "handle": handle,
        "url": raw.get("public_url") or base_url.rstrip("/") + "/products/" + urllib.parse.quote(handle),
        "body_html": raw.get("post_content") or raw.get("short_content") or "",
        "vendor": "",
        "product_type": "",
        "tags": [],
        "created_at": raw.get("created_at") or raw.get("created_time") or raw.get("created_at_gmt") or "",
        "published_at": raw.get("published_at") or raw.get("shelved_at") or "",
        "updated_at": raw.get("updated_at") or raw.get("updated_time") or raw.get("updated_at_gmt") or "",
        "price_min": min(prices) if prices else None,
        "price_max": max(prices) if prices else None,
        "image": image,
        "variants": variants,
        "images": gallery,
        "raw": raw,
    }
