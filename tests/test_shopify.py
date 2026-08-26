from monitor.adapters.shopify import normalize_product


def test_normalize_product_extracts_core_fields():
    raw = {
        "id": 123,
        "title": "Test Product",
        "handle": "test-product",
        "vendor": "Vendor",
        "product_type": "Type",
        "tags": ["new", "sale"],
        "created_at": "2026-08-25T01:00:00-08:00",
        "published_at": "2026-08-25T01:01:00-08:00",
        "updated_at": "2026-08-25T01:02:00-08:00",
        "variants": [
            {"id": 1, "price": "10.00"},
            {"id": 2, "price": "15.50"},
        ],
        "images": [{"src": "https://cdn.example.com/a.jpg"}],
        "body_html": "<p>Hello</p>",
    }

    product = normalize_product("https://example.com", raw)

    assert product["id"] == "123"
    assert product["url"] == "https://example.com/products/test-product"
    assert product["price_min"] == 10.0
    assert product["price_max"] == 15.5
    assert product["image"] == "https://cdn.example.com/a.jpg"
    assert product["published_at"] == "2026-08-25T01:01:00-08:00"
