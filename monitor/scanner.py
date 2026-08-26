from __future__ import annotations

from dataclasses import dataclass

from . import db
from .adapters.shopify import AdapterError, get_adapter
from .config import AppConfig, SiteConfig
from .notifiers.feishu import FeishuWebhookNotifier, NotifyError


@dataclass
class ScanResult:
    site_id: str
    scan_type: str
    product_count: int
    new_count: int
    pages: int
    notified: bool


def scan_site(config: AppConfig, site: SiteConfig, notify: bool = True, full: bool | None = None, resume: bool = False, from_page: int = 1) -> ScanResult:
    db.init_db(config.storage.path)
    notifier = FeishuWebhookNotifier(config.feishu.webhook_url, config.feishu.secret)
    with db.db(config.storage.path) as conn:
        db.upsert_site(conn, site)
        baseline_done = db.baseline_complete(conn, site.id)
        scan_type = "full" if (full is True or not baseline_done) else "incremental"
        max_pages = site.full_scan_pages if scan_type == "full" else site.incremental_pages
        if resume and scan_type == "full":
            start_page = max(1, db.get_scan_cursor(conn, site.id), from_page)
            max_pages = max(1, site.full_scan_pages - start_page + 1)
        else:
            start_page = 1
        run_id = db.start_scan(conn, site.id, scan_type)
        total_products = 0
        new_total = 0
        try:
            adapter = get_adapter(site.adapter, site.base_url)
            event_ids: list[int] = []
            all_new_products: list[dict] = []
            pages = 0
            should_notify_new = bool(site.notify.get("new_product", True)) and baseline_done and notify
            if scan_type == "full" and start_page > 1:
                total_products = 0
            for page, products in adapter.iter_product_pages(max_pages=max_pages, start_page=start_page):
                pages = page
                total_products += len(products)
                new_products = db.upsert_products(conn, site.id, products)
                if baseline_done:
                    new_total += len(new_products)
                    all_new_products.extend(new_products)
                    for product in new_products:
                        event_id = db.insert_event(conn, site.id, "new_product", str(product["id"]), product.get("title"), {"product": product}, notified=False)
                        event_ids.append(event_id)
                db.finish_scan(conn, run_id, "running", total_products, new_total)
                db.set_scan_cursor(conn, site.id, page + 1)
                conn.commit()
            did_notify = False
            if should_notify_new and all_new_products:
                text = format_new_products(site, all_new_products)
                try:
                    notifier.send_text(text)
                    db.set_events_notified(conn, event_ids)
                    did_notify = True
                except NotifyError as exc:
                    db.insert_event(conn, site.id, "notify_error", None, "Feishu notify failed", {"error": str(exc)}, notified=False)
            if scan_type == "full" and not baseline_done:
                db.set_baseline_complete(conn, site.id, True)
                db.reset_scan_cursor(conn, site.id)
            db.finish_scan(conn, run_id, "success", total_products, new_total)
            return ScanResult(site.id, scan_type, total_products, new_total, pages, did_notify)
        except AdapterError as exc:
            db.finish_scan(conn, run_id, "failed", total_products, new_total, str(exc))
            db.insert_event(conn, site.id, "scan_error", None, "Scan failed", {"error": str(exc)}, notified=False)
            if notify and site.notify.get("error", True):
                try:
                    notifier.send_text(f"[{site.name}] 扫描失败\n{exc}")
                except NotifyError:
                    pass
            raise


def format_new_products(site: SiteConfig, products: list[dict]) -> str:
    lines = [f"[{site.name}] 发现 {len(products)} 个新品", ""]
    for i, product in enumerate(products[:10], 1):
        price = _price(product)
        lines.extend([
            f"{i}. {product.get('title', '')}",
            f"上架：{product.get('published_at') or product.get('created_at') or '-'}",
            f"价格：{price}",
            f"链接：{product.get('url', '')}",
            "",
        ])
    if len(products) > 10:
        lines.append(f"还有 {len(products) - 10} 个新品未展示，请导出查看。")
    return "\n".join(lines).strip()


def _price(product: dict) -> str:
    min_price = product.get("price_min")
    max_price = product.get("price_max")
    if min_price is None and max_price is None:
        return "-"
    if min_price == max_price:
        return str(min_price)
    return f"{min_price} - {max_price}"
