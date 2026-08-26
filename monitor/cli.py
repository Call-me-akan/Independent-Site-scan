from __future__ import annotations

import argparse
import sys
import time

from . import db
from .config import AppConfig, SiteConfig, get_site, init_config, load_config, save_config

from .exporters import export_products
from .notifiers.feishu import FeishuWebhookNotifier
from .scanner import scan_site


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="monitor", description="Independent store product monitor")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("init", help="create config.yaml and initialize database")

    add = sub.add_parser("add-site", help="add or update a monitored site")
    add.add_argument("--id", required=True)
    add.add_argument("--url", required=True)
    add.add_argument("--name", default="")
    add.add_argument("--adapter", default="shopify_products_json")
    add.add_argument("--interval", type=int, default=15)

    scan = sub.add_parser("scan", help="scan one site or all sites once")
    scan.add_argument("--site")
    scan.add_argument("--all", action="store_true")
    scan.add_argument("--full", action="store_true")
    scan.add_argument("--resume", action="store_true")
    scan.add_argument("--from-page", type=int, default=1)
    scan.add_argument("--no-notify", action="store_true")

    run = sub.add_parser("run", help="run daemon loop")
    run.add_argument("--once", action="store_true")

    export = sub.add_parser("export", help="export products")
    export.add_argument("--site", required=True)
    export.add_argument("--format", choices=["csv", "json"], default="csv")

    sub.add_parser("status", help="show scan status")
    sub.add_parser("list-sites", help="list configured sites")
    sub.add_parser("test-feishu", help="send a Feishu test message")

    args = parser.parse_args(argv)
    if args.command == "init":
        config_path = init_config()
        config = load_config(config_path)
        db.init_db(config.storage.path)
        with db.db(config.storage.path) as conn:
            for site in config.sites:
                db.upsert_site(conn, site)
        print(f"Config ready: {config_path}")
        print(f"Database ready: {config.storage.path}")
        print(f"Sites initialized: {len(config.sites)}")
        return 0

    config = load_config()
    db.init_db(config.storage.path)

    if args.command == "add-site":
        site = SiteConfig(
            id=args.id,
            name=args.name or args.id,
            base_url=args.url.rstrip("/"),
            adapter=args.adapter,
            interval_minutes=args.interval,
            enabled=True,
            full_scan_pages=40,
            incremental_pages=1,
            notify={"new_product": True, "price_change": False, "update": False, "error": True},
        )
        config.sites = [s for s in config.sites if s.id != site.id] + [site]
        save_config(config)
        with db.db(config.storage.path) as conn:
            db.upsert_site(conn, site)
        print(f"Site saved: {site.id} {site.base_url}")
        return 0

    if args.command == "scan":
        sites = config.sites if args.all else [get_site(config, args.site)]
        for site in sites:
            if not site.enabled:
                print(f"skip disabled site: {site.id}")
                continue
            result = scan_site(config, site, notify=not args.no_notify, full=args.full or None, resume=args.resume, from_page=args.from_page)
            print(f"{result.site_id}: {result.scan_type}, products={result.product_count}, new={result.new_count}, pages={result.pages}, notified={result.notified}")
        return 0

    if args.command == "run":
        return run_loop(config, once=args.once)

    if args.command == "export":
        path = export_products(config.storage.path, config.export.dir, args.site, args.format)
        print(f"Exported: {path}")
        return 0

    if args.command == "status":
        with db.db(config.storage.path) as conn:
            rows = db.recent_scan_status(conn)
        if not rows:
            print("No sites initialized")
            return 0
        for row in rows:
            print(f"{row['id']} | base={row['baseline_complete']} | cursor={row['full_scan_cursor_page']} | products={row['product_count']} | last={row['status'] or '-'} | new={row['new_count'] or 0} | finished={row['finished_at'] or '-'} | {row['error_message'] or ''}")
        return 0

    if args.command == "list-sites":
        for site in config.sites:
            print(f"{site.id}\t{site.base_url}\t{site.adapter}\tenabled={site.enabled}\tinterval={site.interval_minutes}m")
        return 0

    if args.command == "test-feishu":
        notifier = FeishuWebhookNotifier(config.feishu.webhook_url, config.feishu.secret)
        if not notifier.enabled():
            print("Feishu webhook_url is empty in config.yaml")
            return 2
        notifier.send_text("独立站商品监控 Agent 测试消息")
        print("Feishu test message sent")
        return 0

    parser.print_help()
    return 1


def run_loop(config: AppConfig, once: bool = False) -> int:
    next_due = {site.id: 0.0 for site in config.sites if site.enabled}
    print("monitor daemon started. Press Ctrl+C to stop.", flush=True)
    try:
        while True:
            now = time.time()
            for site in config.sites:
                if not site.enabled:
                    continue
                if now < next_due.get(site.id, 0):
                    continue
                try:
                    result = scan_site(config, site, notify=True, full=None)
                    print(f"{site.id}: {result.scan_type}, products={result.product_count}, new={result.new_count}", flush=True)
                except Exception as exc:  # noqa: BLE001
                    print(f"{site.id}: scan failed: {exc}", file=sys.stderr, flush=True)
                next_due[site.id] = time.time() + max(1, site.interval_minutes) * 60
            if once:
                return 0
            time.sleep(5)
    except KeyboardInterrupt:
        print("stopped", flush=True)
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
