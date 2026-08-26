# Independent-Site-scan / 独立站上新监控 Agent

一个本地运行的独立站商品监控工具，优先支持 Shopify `/products.json`。

## 功能

- 监控多个站点
- 首次全量建立基线
- 后续增量扫描新品
- 记录商品上架时间 `created_at` / `published_at`
- 导出 CSV / JSON
- 飞书 webhook 通知
- SQLite 本地存储
- GitHub Actions CI 与 Release 打包

## 快速开始

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
pip install -e .
python -m monitor init
python -m monitor list-sites
python -m monitor scan --site viqzes --no-notify
python -m monitor export --site viqzes --format csv
```

Windows PowerShell：

```powershell
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements-dev.txt
pip install -e .
python -m monitor init
```

## 配置

编辑 `config.yaml`：

- `sites`：站点列表
- `feishu.webhook_url`：飞书机器人 webhook
- `feishu.secret`：飞书机器人签名密钥，可为空
- `storage.path`：SQLite 路径
- `export.dir`：导出目录

本地敏感文件不会进 Git：

- `config.yaml`
- `data/`
- `exports/`

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

## 本地常驻运行

```bash
scripts/start-daemon.sh
scripts/status-daemon.sh
scripts/stop-daemon.sh
```

日志位置：

```text
logs/monitor.log
```

进程 PID：

```text
monitor.pid
```

## WebUI（本地管理面板）

启动本地 WebUI：

```bash
python -m monitor web
```

启动后会自动打开浏览器：

```text
http://127.0.0.1:8321
```

WebUI 提供：

- 站点管理：添加 / 删除 / 启用停用
- 手动扫描单个站点
- 商品查询（按站点 / 关键词）
- 商品导出 CSV / JSON
- 最近事件查看
- 飞书 Webhook 配置与测试

常用参数：

```bash
python -m monitor web --port 9000          # 自定义端口
python -m monitor web --no-browser          # 不自动打开浏览器
```

## CI

每次 push / pull request 会运行：

- 安装依赖
- `python -m compileall monitor`
- `pytest -q`
- CLI smoke test

## Release 打包

推送 tag 会触发 `.github/workflows/release.yml`，自动构建：

- `monitor-linux`
- `monitor-macos`
- `monitor-windows.exe`

示例：

```bash
git tag v0.1.0
git push origin v0.1.0
```

本地 macOS 打包：

```bash
pip install -r requirements-dev.txt
scripts/build-mac.sh
./dist/monitor status
```

Windows 本地打包：

```bat
pip install -r requirements-dev.txt
scripts\build-win.bat
```

## Docker

```bash
docker build -t store-monitor-agent .
docker run --rm -it \
  -v "$PWD/config.yaml:/app/config.yaml" \
  -v "$PWD/data:/app/data" \
  -v "$PWD/exports:/app/exports" \
  store-monitor-agent
```
