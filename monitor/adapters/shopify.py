from __future__ import annotations

import json
import time
import urllib.error
import urllib.parse
import urllib.request

from .base import AdapterError, FetchResult, float_or_none



class ShopifyProductsJsonAdapter:
    name = "shopify_products_json"

    def __init__(self, base_url: str, timeout: int = 20):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def iter_product_pages(self, max_pages: int = 1, start_page: int = 1):
        seen: set[str] = set()
        for page in range(start_page, start_page + max_pages):
            data = self._get_json(f"/products.json?limit=250&page={page}")
            products = data.get("products")
            if not isinstance(products, list):
                raise AdapterError("Invalid Shopify response: missing products list")
            if not products:
                break
            normalized = []
            for raw in products:
                product = normalize_product(self.base_url, raw)
                product_id = str(product.get("id") or product.get("handle"))
                if product_id and product_id not in seen:
                    seen.add(product_id)
                    normalized.append(product)
            yield page, normalized
            if len(products) < 250:
                break
            time.sleep(0.2)

    def fetch_products(self, max_pages: int = 1) -> FetchResult:
        all_products: list[dict] = []
        pages = 0
        for page, products in self.iter_product_pages(max_pages=max_pages):
            all_products.extend(products)
            pages = page
        return FetchResult(products=all_products, pages=pages)

    def _get_json(self, path: str) -> dict:
        url = self.base_url + path
        req = urllib.request.Request(
            url,
            headers={
                "Accept": "application/json,text/plain,*/*",
                "User-Agent": "Mozilla/5.0 StoreMonitorAgent/0.1",
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                status = getattr(resp, "status", 200)
                body = resp.read()
                content_type = resp.headers.get("content-type", "")
        except urllib.error.HTTPError as exc:
            raise AdapterError(f"HTTP {exc.code}: {url}") from exc
        except urllib.error.URLError as exc:
            raise AdapterError(f"Request failed: {url}: {exc.reason}") from exc
        if status < 200 or status >= 300:
            raise AdapterError(f"HTTP {status}: {url}")
        text = body.decode("utf-8", errors="replace")
        lowered = text[:500].lower()
        if "text/html" in content_type.lower() or "<html" in lowered or "just a moment" in lowered or "verifying your connection" in lowered:
            raise AdapterError(f"Unexpected HTML/challenge page: {url}")
        try:
            return json.loads(text)
        except json.JSONDecodeError as exc:
            raise AdapterError(f"JSON parse failed at page {url}: {exc}") from exc


def normalize_product(base_url: str, raw: dict) -> dict:
    variants = raw.get("variants") or []
    prices = [float_or_none(v.get("price")) for v in variants]
    prices = [p for p in prices if p is not None]
    images = raw.get("images") or []
    handle = raw.get("handle") or ""
    return {
        "id": str(raw.get("id") or handle),
        "title": raw.get("title") or "",
        "handle": handle,
        "url": base_url.rstrip("/") + "/products/" + urllib.parse.quote(handle),
        "body_html": raw.get("body_html") or "",
        "vendor": raw.get("vendor") or "",
        "product_type": raw.get("product_type") or "",
        "tags": raw.get("tags") or [],
        "created_at": raw.get("created_at") or "",
        "published_at": raw.get("published_at") or "",
        "updated_at": raw.get("updated_at") or "",
        "price_min": min(prices) if prices else None,
        "price_max": max(prices) if prices else None,
        "image": images[0].get("src", "") if images else "",
        "variants": variants,
        "images": images,
        "raw": raw,
    }

