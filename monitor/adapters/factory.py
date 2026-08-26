from __future__ import annotations

from .base import AdapterError
from .embedded import EmbeddedPageProductsAdapter
from .shopify import ShopifyProductsJsonAdapter


def get_adapter(adapter_name: str, base_url: str, source_url: str = ""):
    if adapter_name == ShopifyProductsJsonAdapter.name:
        return ShopifyProductsJsonAdapter(base_url)
    if adapter_name == EmbeddedPageProductsAdapter.name:
        return EmbeddedPageProductsAdapter(base_url, source_url=source_url)
    raise AdapterError(f"Unsupported adapter: {adapter_name}")
