# Independent-Site-scan / 独立站上新监控 Agent

一个本地运行的**独立站商品监控工具**：定时扫描多个独立站，发现新品后推送到飞书，并提供 Web 管理面板与 CSV/JSON 导出。

## 特性

- 📡 多站点监控：支持 Shopify（`/products.json`）与页面内嵌商品 JSON 的独立站
- ⏱ 首扫建立基线，之后增量扫描，只报新品
- 🕒 记录每个商品的上架时间（`created_at` / `published_at`）
- 🔔 飞书通知：**卡片消息**（标题 + 商品信息 + 跳转按钮）
- 🌐 本地 WebUI：站点管理、手动扫描、商品查询、导出、飞书配置
- 🗄 SQLite 本地存储，CSV / JSON 导出
- 💻 Windows / macOS / Linux 可执行文件，Docker 支持
- ⚙️ GitHub Actions CI + Release 自动打包

## 快速开始

> 两种方式：**直接下载可执行文件**（推荐给非开发者）或 **源码运行**（推荐给开发者）。

### 方式 A：下载 Release 可执行文件（无需安装 Python）

1. 打开 [Releases](https://github.com/Call-me-akan/Independent-Site-scan/releases)
2. 下载对应系统的文件：
   - Windows：`monitor-windows.exe`
   - macOS：`monitor-macos`
   - Linux：`monitor-linux`
3. 双击运行（macOS 需 `chmod +x monitor-macos`）：
   ```bash
   ./monitor-macos web
   ```
4. 浏览器自动打开 `http://127.0.0.1:8321`，首次启动自动生成配置

### 方式 B：源码运行

```bash
git clone git@github.com:Call-me-akan/Independent-Site-scan.git
cd Independent-Site-scan

# macOS / Linux
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
pip install -e .

# Windows PowerShell
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements-dev.txt
pip install -e .
```

## 配置

### 1. 初始化

```bash
python -m monitor init
```

生成 `config.yaml` 和数据库 `data/monitor.db`。

### 2. 配置通知（可选但推荐）

支持 **飞书** 和 **钉钉** 两个机器人（可同时启用），只需其中之一也可。

**飞书**：在飞书群添加「自定义机器人」，拿到 Webhook，填入 `config.yaml`：

```yaml
feishu:
  webhook_url: "https://open.feishu.cn/open-apis/bot/v2/hook/xxxx"
  secret: ""            # 若开启签名校验则填写
```

**钉钉**：在钉钉群添加「自定义机器人」（安全设置选加签），填入 `config.yaml`：

```yaml
dingtalk:
  webhook_url: "https://oapi.dingtalk.com/robot/send?access_token=xxxx"
  secret: "SECxxx"      # 加签密钥
```

测试通知：

```bash
python -m monitor test-feishu
python -m monitor test-dingtalk
```

### 3. 添加站点

Shopify 站点：

```bash
python -m monitor add-site --id viqzes --url https://viqzes.com --adapter shopify_products_json
```

页面内嵌商品 JSON 的独立站（如 webfastcdn / techcloud）：

```bash
python -m monitor add-site \
  --id breliance \
  --url https://www.breliance.com \
  --source-url "https://www.breliance.com/collections/all?&type=collections&page_size=48&sort=created-descending&slug=all" \
  --adapter embedded_page_products
```

### 4. 首次扫描（建立基线，不推送）

```bash
python -m monitor scan --all --no-notify
```

之后的扫描是增量的，只推送新出现的商品。

## WebUI 使用

```bash
python -m monitor web            # 启动，自动打开浏览器
python -m monitor web --port 9000
```

打开 http://127.0.0.1:8321 后可以：

- **监控总览**：所有站点状态卡片（商品数 / 扫描状态 / 新品数），一键扫描、启停、删除
- **商品**：按站点和关键词查询商品，导出 CSV / JSON
- **事件**：最近的新品 / 错误记录
- **飞书设置**：配置 Webhook 并发测试消息

## 通知格式

新品通知同时支持飞书卡片与钉钉 markdown：

**飞书（交互卡片）：**

```text
┌─ [viqzes] 发现 3 个新品（最新 3 个） ─────┐
│ **商品标题**                              │
│ 💰 9.99  ·  🆕 2026-08-27              │
│ 🔗 https://viqzes.com/products/xxx      │
│ ...                                      │
│ [打开商品]                               │
└──────────────────────────────────────────┘
```

**钉钉（markdown，支持商品缩略图）：**

```text
[viqzes] 发现 3 个新品（最新 3 个）
**商品标题**
💰 9.99 · 🆕 2026-08-27
![商品缩略图](https://cdn.shopify.com/...)
[查看商品](https://viqzes.com/products/xxx)
---
（下一个商品）
```

> 注：飞书自定义机器人卡片不支持内嵌远程图片（需 image_key），商品图以 URL 文字展示；钉钉 markdown 原生支持远程图片，会直接渲染缩略图。

## CLI 命令

| 命令 | 说明 |
|---|---|
| `monitor init` | 初始化配置和数据库 |
| `monitor add-site` | 添加/更新站点 |
| `monitor scan --site <id>` | 扫描单个站点 |
| `monitor scan --all` | 扫描全部站点 |
| `monitor scan --site <id> --resume --from-page N` | 从第 N 页续扫（大站断点续扫） |
| `monitor run` | 常驻后台轮询（按站点间隔） |
| `monitor status` | 查看所有站点状态 |
| `monitor export --site <id> --format csv/json` | 导出商品数据 |
| `monitor test-feishu` | 发送飞书测试消息 |
| `monitor test-dingtalk` | 发送钉钉测试消息 |

## 本地常驻运行

```bash
scripts/start-daemon.sh     # 启动后台监控
scripts/status-daemon.sh    # 查看状态
scripts/stop-daemon.sh      # 停止
```

日志：`logs/monitor.log` · PID：`monitor.pid`

## 适配器

| 适配器 | 适用站点 | 上架时间 |
|---|---|---|
| `shopify_products_json` | Shopify 独立站（开放 `/products.json`） | ✅ 真实 `published_at` |
| `embedded_page_products` | webfastcdn / techcloud 等页面内嵌商品 JSON | ⚠️ 部分站点缺失，用首次发现时间兜底 |

## 开发

```bash
pytest -q                    # 测试
python -m compileall monitor # 语法检查
```

## 打包

GitHub Release（推送 tag 自动构建三端）：

```bash
git tag v0.2.0
git push origin v0.2.0
```

本地打包：

```bash
# macOS
pip install -r requirements-dev.txt
scripts/build-mac.sh

# Windows
pip install -r requirements-dev.txt
scripts\build-win.bat
```

产物在 `dist/monitor`，开箱即用（无需 Python 环境）。

> macOS 用户若从网上下载/收到别人给的二进制，首次运行可能被 Gatekeeper 拦截，解除方法见 [docs/macos-gatekeeper-zh.md](docs/macos-gatekeeper-zh.md)，或执行 `./scripts/unlock-macos.sh <路径>`。

## Docker

```bash
docker build -t store-monitor-agent .
docker run --rm -it \
  -v "$PWD/config.yaml:/app/config.yaml" \
  -v "$PWD/data:/app/data" \
  -v "$PWD/exports:/app/exports" \
  store-monitor-agent
```

## 常见问题

**Q：启动 WebUI 后需要配置什么才能用？**
首次启动会自动生成 `config.yaml`。建议先做两件事：在「飞书设置」里填 Webhook，在「监控总览」里添加站点并点击扫描。

**Q：扫描时说 URL 返回 404？**
该站可能没有开放 `/products.json`。Shopify 站都用它；其他独立站请改用 `embedded_page_products` 适配器（`--source-url` 指向商品列表页）。

**Q：飞书/钉钉没收到消息？**
1. 先 `python -m monitor test-feishu` / `test-dingtalk`，群里有消息则链路正常
2. 首次扫描（建基线）不会推送，只有之后的新品才推送
3. 若在「自定义关键词」安全校验，消息需包含关键词才会被转发

**Q：如何让陌生人直接用？**
发给他 Release 里的可执行文件即可，双击运行 WebUI，无需安装 Python。配置和数据都保存在运行目录下的 `config.yaml` 和 `data/`。

## 目录结构

```text
monitor/
  cli.py            # 命令行入口
  scanner.py        # 扫描与新品检测
  db.py             # SQLite 存储
  config.py         # 配置
  exporters.py      # CSV/JSON 导出
  webui.py          # Flask 本地 WebUI
  adapters/         # 站点适配器（shopify / embedded）
  notifiers/        # 通知器（feishu）
scripts/            # 启动/停止/打包脚本
.github/workflows/  # CI / Release
```

> 安全说明：`config.yaml`（含飞书 Webhook）、`data/`、`exports/`、`logs/` 均不会进入 Git 仓库。