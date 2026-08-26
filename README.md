# 独立站上新监控 Agent

一个本地运行的独立站商品监控工具，优先支持 Shopify `/products.json`。

## 功能

- 监控多个站点
- 首次全量建立基线
- 后续增量扫描新品
- 记录商品上架时间 `created_at` / `published_at`
- 导出 CSV / JSON
- 飞书 webhook 通知
- SQLite 本地存储

## 快速开始

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m monitor init
python -m monitor list-sites
python -m monitor scan --site viqzes --no-notify
python -m monitor export --site viqzes --format csv
```

## 配置

编辑 `config.yaml`：

- `sites`：站点列表
- `feishu.webhook_url`：飞书机器人 webhook
- `storage.path`：SQLite 路径
- `export.dir`：导出目录

## CLI

```bash
monitor init
monitor add-site --id viqzes --url https://viqzes.com
monitor scan --site viqzes
monitor scan --site viqzes --resume --from-page 9
monitor run
monitor status
monitor export --site viqzes --format csv
monitor test-feishu
```

## 打包

后续可用 PyInstaller 打成 Windows/macOS 可执行文件，再补 Dockerfile 做容器化。
