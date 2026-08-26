from monitor.adapters.embedded import extract_products_from_html, normalize_embedded_product, set_page_param


def test_embedded_extracts_shop_json_products():
    html = '''
    <script type="shop/json" data-type-id="search-page">
    {"current_page":1,"data":[{"ID":20000721,"title":"Test Item","slug":"test-item","min_price":12.99,"max_price":15.99,"public_url":"https://example.com/products/test-item","gallery":[{"url":"https://cdn.example.com/a.png"}],"variants":[{"ID":1,"price":12.99,"sku":"A"}]}]}
    </script>
    '''
    products = extract_products_from_html(html)
    assert len(products) == 1
    product = normalize_embedded_product("https://example.com", products[0])
    assert product["id"] == "20000721"
    assert product["handle"] == "test-item"
    assert product["price_min"] == 12.99
    assert product["price_max"] == 15.99
    assert product["image"] == "https://cdn.example.com/a.png"


def test_set_page_param_replaces_existing_page():
    assert set_page_param("https://example.com/search?q=&page=1", 3) == "https://example.com/search?q=&page=3"
