"""Local WebUI for store monitor agent.

A single-file Flask app with an embedded frontend page, so it can be
packed into a single executable easily (no external templates/static).
"""
from __future__ import annotations

import threading
import webbrowser
from pathlib import Path

from . import db
from .config import get_site, load_config, save_config
from .exporters import export_products
from .notifiers.feishu import FeishuWebhookNotifier

try:
    from flask import Flask, Response, jsonify, request, send_file
except ImportError as exc:  # pragma: no cover
    raise SystemExit("Missing dependency: Flask. Run: pip install -r requirements.txt") from exc

from .adapters.base import AdapterError
from .scanner import scan_site
from .config import SiteConfig


def create_app(config_path: str = "config.yaml") -> Flask:
    app = Flask(__name__)
    app.config["CONFIG_PATH"] = config_path

    def load() -> object:
        return load_config(Path(config_path))

    # ---------- status ----------

    @app.get("/api/status")
    def api_status():
        cfg = load()
        db.init_db(cfg.storage.path)
        with db.db(cfg.storage.path) as conn:
            rows = db.recent_scan_status(conn)
            by_site = {r["id"]: dict(r) for r in rows}
        sites = []
        for site in cfg.sites:
            info = by_site.get(site.id, {})
            sites.append({
                "id": site.id,
                "name": site.name,
                "base_url": site.base_url,
                "adapter": site.adapter,
                "enabled": bool(site.enabled),
                "interval_minutes": site.interval_minutes,
                "products": info.get("product_count", 0),
                "status": info.get("status"),
                "new": info.get("new_count", 0),
                "finished_at": info.get("finished_at"),
                "error": info.get("error_message"),
            })
        return jsonify({
            "sites": sites,
            "feishu_configured": bool(cfg.feishu.webhook_url),
        })

    # ---------- site management ----------

    @app.post("/api/sites")
    def api_add_site():
        cfg = load()
        data = request.get_json(force=True)
        site_id = str(data.get("id") or "").strip()
        if not site_id:
            return jsonify({"error": "id is required"}), 400
        if not data.get("url"):
            return jsonify({"error": "url is required"}), 400
        site = SiteConfig(
            id=site_id,
            name=str(data.get("name") or site_id),
            base_url=str(data["url"]).rstrip("/"),
            source_url=str(data.get("source_url") or ""),
            adapter=str(data.get("adapter") or "shopify_products_json"),
            interval_minutes=int(data.get("interval") or 15),
            enabled=bool(data.get("enabled", True)),
            full_scan_pages=int(data.get("full_scan_pages") or 40),
            incremental_pages=1,
            notify={"new_product": True, "price_change": False, "update": False, "error": True},
        )
        cfg.sites = [s for s in cfg.sites if s.id != site.id] + [site]
        save_config(cfg, Path(config_path))
        with db.db(cfg.storage.path) as conn:
            db.upsert_site(conn, site)
        return jsonify({"ok": True, "id": site_id})

    @app.delete("/api/sites/<site_id>")
    def api_delete_site(site_id):
        cfg = load()
        cfg.sites = [s for s in cfg.sites if s.id != site_id]
        save_config(cfg, Path(config_path))
        return jsonify({"ok": True})

    @app.post("/api/sites/<site_id>/toggle")
    def api_toggle_site(site_id):
        cfg = load()
        site = get_site(cfg, site_id)
        site.enabled = not site.enabled
        save_config(cfg, Path(config_path))
        with db.db(cfg.storage.path) as conn:
            db.upsert_site(conn, site)
        return jsonify({"ok": True, "enabled": site.enabled})

    # ---------- scan ----------

    @app.post("/api/sites/<site_id>/scan")
    def api_scan_site(site_id):
        cfg = load()
        site = get_site(cfg, site_id)
        data = request.get_json(silent=True) or {}
        try:
            result = scan_site(cfg, site, notify=bool(data.get("notify", True)), full=bool(data.get("full")), resume=False)
            return jsonify({
                "ok": True,
                "site_id": result.site_id,
                "scan_type": result.scan_type,
                "products": result.product_count,
                "new": result.new_count,
                "pages": result.pages,
                "notified": result.notified,
            })
        except AdapterError as exc:
            return jsonify({"ok": False, "error": str(exc)}), 500

    # ---------- products ----------

    @app.get("/api/products")
    def api_products():
        cfg = load()
        site_id = request.args.get("site", "")
        keyword = (request.args.get("q") or "").strip().lower()
        limit = min(int(request.args.get("limit") or 200), 1000)
        db.init_db(cfg.storage.path)
        with db.db(cfg.storage.path) as conn:
            rows = db.products_for_export(conn, site_id) if site_id else []
        items = []
        for row in rows:
            title = row["title"] or ""
            if keyword and keyword not in (title + " " + (row["handle"] or "")).lower():
                continue
            items.append({
                "id": row["product_id"],
                "title": title,
                "handle": row["handle"],
                "url": row["url"],
                "published": row["published_at_remote"] or row["created_at_remote"] or "",
                "price_min": row["price_min"],
                "price_max": row["price_max"],
                "image": row["image"],
            })
            if len(items) >= limit:
                break
        return jsonify({"products": items, "count": len(items)})

    # ---------- events ----------

    @app.get("/api/events")
    def api_events():
        cfg = load()
        site_id = request.args.get("site", "")
        limit = min(int(request.args.get("limit") or 50), 500)
        db.init_db(cfg.storage.path)
        with db.db(cfg.storage.path) as conn:
            if site_id:
                rows = conn.execute(
                    "SELECT * FROM events WHERE site_id = ? ORDER BY id DESC LIMIT ?",
                    (site_id, limit),
                ).fetchall()
            else:
                rows = conn.execute("SELECT * FROM events ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
        return jsonify({
            "events": [dict(r) for r in rows],
        })

    # ---------- feishu ----------

    @app.get("/api/feishu")
    def api_feishu_get():
        cfg = load()
        return jsonify({
            "configured": bool(cfg.feishu.webhook_url),
            "webhook_hint": (cfg.feishu.webhook_url[:40] + "…") if cfg.feishu.webhook_url else "",
            "has_secret": bool(cfg.feishu.secret),
        })

    @app.post("/api/feishu")
    def api_feishu_set():
        cfg = load()
        data = request.get_json(force=True)
        if "webhook_url" in data:
            cfg.feishu.webhook_url = str(data.get("webhook_url") or "").strip()
        if "secret" in data:
            cfg.feishu.secret = str(data.get("secret") or "").strip()
        save_config(cfg, Path(config_path))
        return jsonify({"ok": True})

    @app.post("/api/feishu/test")
    def api_feishu_test():
        cfg = load()
        notifier = FeishuWebhookNotifier(cfg.feishu.webhook_url, cfg.feishu.secret)
        if not notifier.enabled():
            return jsonify({"ok": False, "error": "webhook_url is empty"}), 400
        try:
            notifier.send_text("独立站商品监控 Agent WebUI 测试消息")
            return jsonify({"ok": True})
        except Exception as exc:
            return jsonify({"ok": False, "error": str(exc)}), 500

    # ---------- export ----------

    @app.get("/api/export")
    def api_export():
        cfg = load()
        site_id = request.args.get("site", "")
        fmt = request.args.get("format", "csv")
        if not site_id:
            return jsonify({"error": "site required"}), 400
        try:
            path = export_products(cfg.storage.path, cfg.export.dir, site_id, fmt)
            path = Path(path).resolve()
            return send_file(str(path), as_attachment=True, download_name=path.name)
        except Exception as exc:
            return jsonify({"error": str(exc)}), 500

    # ---------- index ----------

    @app.get("/")
    def index():
        return Response(INDEX_HTML, mimetype="text/html")

    return app


def run_web(config_path: str = "config.yaml", host: str = "127.0.0.1", port: int = 8321, open_browser: bool = True) -> None:
    cfg_path = Path(config_path)
    if not cfg_path.exists():
        from .config import init_config as _init_config

        _init_config(cfg_path)
        print(f"Config auto-created: {cfg_path}", flush=True)
    cfg = load_config(cfg_path)
    db.init_db(cfg.storage.path)
    app = create_app(config_path)
    if open_browser:
        threading.Timer(0.8, lambda: webbrowser.open(f"http://{host}:{port}")).start()
    print(f"WebUI running at http://{host}:{port} (Ctrl+C to stop)", flush=True)
    app.run(host=host, port=port, debug=False, use_reloader=False)


INDEX_HTML = r"""<!doctype html>
<html lang="zh">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>独立站商品监控 Agent</title>
<style>
:root{--bg:#f5f6f8;--card:#fff;--line:#e3e7ec;--text:#1c2733;--muted:#6b7785;--accent:#1677c8;--danger:#c0392b;--ok:#27ae60}
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","PingFang SC","Microsoft YaHei",sans-serif;background:var(--bg);color:var(--text);font-size:14px}
header{background:#14212b;color:#fff;padding:14px 24px;display:flex;align-items:center;gap:12px;position:sticky;top:0;z-index:10}
header h1{font-size:16px;font-weight:600}
header .sub{color:#9fb2c2;font-size:12px;margin-left:auto}
main{padding:20px 24px;max-width:1200px;margin:0 auto}
.card{background:var(--card);border:1px solid var(--line);border-radius:8px;padding:16px;margin-bottom:16px}
.card h2{font-size:14px;margin-bottom:12px;color:#33414f}
.banner{background:#fff8e1;border:1px solid #f5d98e;color:#8a6d1a;padding:10px 14px;border-radius:6px;margin-bottom:16px;display:none}
button{background:#fff;border:1px solid #c3ccd6;border-radius:5px;padding:6px 12px;cursor:pointer;font-size:13px}
button:hover{background:#f0f3f6}
button.primary{background:var(--accent);border-color:var(--accent);color:#fff}
button.danger{background:#fff;border-color:#e3b7b2;color:var(--danger)}
button:disabled{opacity:.5;cursor:not-allowed}
input,select{padding:7px 9px;border:1px solid #c3ccd6;border-radius:5px;font-size:13px;font-family:inherit}
.row{display:flex;gap:8px;flex-wrap:wrap;align-items:center}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:12px}
.site-card{border:1px solid var(--line);border-radius:8px;padding:12px;background:#fbfcfe}
.site-card .head{display:flex;align-items:center;justify-content:space-between;gap:8px;margin-bottom:8px}
.site-card .name{font-weight:600;font-size:14px}
.site-card .url{color:var(--muted);font-size:12px;word-break:break-all;margin-bottom:8px}
.badge{font-size:11px;padding:2px 8px;border-radius:10px;font-weight:500}
.badge.ok{background:#e8f7ee;color:var(--ok)}
.badge.failed{background:#fdeceb;color:var(--danger)}
.badge.running{background:#e8f1fb;color:var(--accent)}
.badge.off{background:#eef1f4;color:var(--muted)}
.site-meta{display:flex;gap:12px;color:var(--muted);font-size:12px;margin-bottom:10px}
table{width:100%;border-collapse:collapse;font-size:13px}
th,td{padding:7px 9px;border-bottom:1px solid var(--line);text-align:left;vertical-align:top}
th{background:#f1f4f6;font-weight:600;color:#44525f;position:sticky;top:0}
td img{width:34px;height:34px;object-fit:cover;border-radius:4px}
.toolbar{display:flex;gap:8px;flex-wrap:wrap;margin-bottom:12px;align-items:center}
.toast{position:fixed;bottom:20px;left:50%;transform:translateX(-50%);background:#14212b;color:#fff;padding:10px 18px;border-radius:6px;font-size:13px;opacity:0;transition:opacity .2s;z-index:99;pointer-events:none}
.toast.show{opacity:1}
a{color:var(--accent);text-decoration:none}
.tabs{display:flex;gap:2px;border-bottom:1px solid var(--line);margin-bottom:16px}
.tab{padding:8px 16px;cursor:pointer;color:var(--muted);border-bottom:2px solid transparent}
.tab.active{color:var(--accent);border-bottom-color:var(--accent);font-weight:600}
.panel{display:none}
.panel.active{display:block}
.empty{color:var(--muted);text-align:center;padding:30px}
@media(max-width:600px){main{padding:12px}header{padding:10px 14px}}
</style>
</head>
<body>
<header>
  <h1>📦 独立站商品监控 Agent</h1>
  <span class="sub" id="feishu-state">飞书未配置</span>
</header>
<main>
  <div class="banner" id="banner">⚠️ 尚未配置飞书 Webhook，添加后新品才会推送到飞书群。<button class="primary" onclick="goTab('feishu')">去配置</button></div>

  <div class="tabs">
    <div class="tab active" data-tab="overview" onclick="goTab('overview')">监控总览</div>
    <div class="tab" data-tab="products" onclick="goTab('products')">商品</div>
    <div class="tab" data-tab="events" onclick="goTab('events')">事件</div>
    <div class="tab" data-tab="feishu" onclick="goTab('feishu')">飞书设置</div>
  </div>

  <!-- overview -->
  <div class="panel active" id="panel-overview">
    <div class="card">
      <div class="row" style="justify-content:space-between">
        <h2>站点列表</h2>
        <button class="primary" onclick="openAddSite()">＋ 添加站点</button>
      </div>
      <div id="site-list" class="grid" style="margin-top:12px"></div>
    </div>
  </div>

  <!-- products -->
  <div class="panel" id="panel-products">
    <div class="card">
      <h2>商品查询</h2>
      <div class="toolbar">
        <select id="prod-site"><option value="">选择站点</option></select>
        <input id="prod-q" placeholder="搜索标题 / handle" style="width:220px">
        <button class="primary" onclick="loadProducts()">查询</button>
        <button onclick="exportCsv()">导出 CSV</button>
        <button onclick="exportJson()">导出 JSON</button>
        <span class="sub" id="prod-count" style="color:var(--muted)"></span>
      </div>
      <div style="max-height:60vh;overflow:auto">
        <table>
          <thead><tr><th></th><th>标题</th><th>价格</th><th>上架时间</th><th></th></tr></thead>
          <tbody id="prod-body"></tbody>
        </table>
      </div>
    </div>
  </div>

  <!-- events -->
  <div class="panel" id="panel-events">
    <div class="card">
      <h2>最近事件</h2>
      <div class="toolbar">
        <select id="event-site"><option value="">全部站点</option></select>
        <button class="primary" onclick="loadEvents()">刷新</button>
      </div>
      <div style="max-height:60vh;overflow:auto">
        <table>
          <thead><tr><th>时间</th><th>站点</th><th>类型</th><th>商品</th></tr></thead>
          <tbody id="event-body"></tbody>
        </table>
      </div>
    </div>
  </div>

  <!-- feishu -->
  <div class="panel" id="panel-feishu">
    <div class="card">
      <h2>飞书 Webhook 设置</h2>
      <div style="display:flex;flex-direction:column;gap:10px;max-width:520px">
        <div><label style="display:block;margin-bottom:4px;color:var(--muted)">Webhook URL</label>
          <input id="fw-url" style="width:100%" placeholder="https://open.feishu.cn/open-apis/bot/v2/hook/xxxx"></div>
        <div><label style="display:block;margin-bottom:4px;color:var(--muted)">签名密钥（可选）</label>
          <input id="fw-secret" style="width:100%" placeholder="SEC..."></div>
        <div class="row">
          <button class="primary" onclick="saveFeishu()">保存</button>
          <button onclick="testFeishu()">发送测试消息</button>
        </div>
      </div>
    </div>
  </div>
</main>
<div class="toast" id="toast"></div>

<!-- add site modal -->
<div id="modal" style="display:none;position:fixed;inset:0;background:#0008;z-index:100;align-items:center;justify-content:center">
  <div style="background:#fff;border-radius:10px;padding:20px;width:min(520px,92vw)">
    <h2 style="margin-bottom:14px">添加站点</h2>
    <div style="display:flex;flex-direction:column;gap:10px">
      <div><label style="display:block;margin-bottom:4px;color:var(--muted)">ID（唯一标识，如 viqzes）</label><input id="a-id" style="width:100%"></div>
      <div><label style="display:block;margin-bottom:4px;color:var(--muted)">名称</label><input id="a-name" style="width:100%"></div>
      <div><label style="display:block;margin-bottom:4px;color:var(--muted)">站点根 URL</label><input id="a-url" style="width:100%" placeholder="https://viqzes.com"></div>
      <div><label style="display:block;margin-bottom:4px;color:var(--muted)">商品列表页 URL（embedded 适配器用，可选）</label><input id="a-source" style="width:100%" placeholder="https://xxx.com/collections/all?..."></div>
      <div><label style="display:block;margin-bottom:4px;color:var(--muted)">适配器</label>
        <select id="a-adapter" style="width:100%">
          <option value="shopify_products_json">Shopify products.json</option>
          <option value="embedded_page_products">页面内嵌商品 JSON</option>
        </select></div>
      <div><label style="display:block;margin-bottom:4px;color:var(--muted)">扫描间隔（分钟）</label><input id="a-interval" type="number" value="15" style="width:100%"></div>
      <div class="row" style="justify-content:flex-end;margin-top:8px">
        <button onclick="closeModal()">取消</button>
        <button class="primary" onclick="submitAddSite()">添加</button>
      </div>
    </div>
  </div>
</div>

<script>
const $=id=>document.getElementById(id);
let state={sites:[]};
function toast(msg){const t=$('toast');t.textContent=msg;t.classList.add('show');setTimeout(()=>t.classList.remove('show'),2500)}
async function api(url,opts){const r=await fetch(url,opts);return r.json()}
function goTab(name){document.querySelectorAll('.tab').forEach(t=>t.classList.toggle('active',t.dataset.tab===name));
  document.querySelectorAll('.panel').forEach(p=>p.classList.toggle('active',p.id==='panel-'+name));
  if(name==='products')initProductTab(); if(name==='events')loadEvents();}
async function loadStatus(){
  state=await api('/api/status');
  const fs=state.feishu_configured;
  $('feishu-state').textContent=fs?'✅ 飞书已配置':'飞书未配置';
  $('banner').style.display=fs?'none':'block';
  renderSites();
  fillSiteSelects();
}
function statusBadge(s){
  if(!s.enabled)return '<span class="badge off">已停用</span>';
  if(s.status==='running')return '<span class="badge running">扫描中</span>';
  if(s.status==='failed')return '<span class="badge failed">异常</span>';
  return s.status==='success'?'<span class="badge ok">正常</span>':'<span class="badge off">待扫描</span>';
}
function renderSites(){
  const el=$('site-list');
  if(!state.sites.length){el.innerHTML='<div class="empty">还没有站点，点右上角「添加站点」开始</div>';return}
  el.innerHTML=state.sites.map(s=>`
    <div class="site-card">
      <div class="head"><span class="name">${esc(s.name)}</span>${statusBadge(s)}</div>
      <div class="url">${esc(s.base_url)}</div>
      <div class="site-meta"><span>商品 ${s.products}</span><span>间隔 ${s.interval_minutes}分</span></div>
      <div class="row">
        <button class="primary" onclick="scanSite('${s.id}')">扫描</button>
        <button onclick="toggleSite('${s.id}')">${s.enabled?'停用':'启用'}</button>
        <button class="danger" onclick="deleteSite('${s.id}','${esc(s.name)}')">删除</button>
      </div>
      ${s.error?`<div style="color:var(--danger);font-size:12px;margin-top:6px">${esc(s.error)}</div>`:''}
    </div>`).join('');
}
function esc(v){return String(v==null?'':v).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]))}
async function scanSite(id){const btn=event.target;btn.disabled=true;btn.textContent='扫描中…';
  const res=await api('/api/sites/'+id+'/scan',{method:'POST',headers:{'Content-Type':'application/json'},body:'{}'});
  btn.disabled=false;btn.textContent='扫描';
  if(res.ok){toast(`扫描完成：${res.products} 个商品，新增 ${res.new} 个`)}else{toast('扫描失败：'+(res.error||'未知'))}
  loadStatus();}
async function toggleSite(id){await api('/api/sites/'+id+'/toggle',{method:'POST'});loadStatus();}
async function deleteSite(id,name){if(!confirm('删除站点 '+name+'？'))return;await api('/api/sites/'+id,{method:'DELETE'});toast('已删除');loadStatus();}
function openAddSite(){$('modal').style.display='flex';$('a-id').focus()}
function closeModal(){$('modal').style.display='none'}
async function submitAddSite(){
  const body={id:$('a-id').value.trim(),name:$('a-name').value.trim(),url:$('a-url').value.trim(),
    source_url:$('a-source').value.trim(),adapter:$('a-adapter').value,interval:Number($('a-interval').value)||15};
  if(!body.id||!body.url){toast('ID 和 URL 必填');return}
  const res=await api('/api/sites',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});
  if(res.ok){toast('站点已添加');closeModal();$('a-id').value='';$('a-name').value='';$('a-url').value='';$('a-source').value='';loadStatus()}
  else toast('添加失败：'+(res.error||'未知'));}
function fillSiteSelects(){const opts='<option value="">全部站点</option>'+state.sites.map(s=>`<option value="${s.id}">${esc(s.name)}</option>`).join('');
  const ps=$('prod-site'),es=$('event-site');
  const keepP=ps.value;ps.innerHTML=opts;if(keepP)ps.value=keepP;
  const keepE=es.value;es.innerHTML=opts;if(keepE)es.value=keepE;}
function initProductTab(){loadProducts()}
async function loadProducts(){
  const site=$('prod-site').value,q=$('prod-q').value.trim();
  const res=await api(`/api/products?site=${encodeURIComponent(site)}&q=${encodeURIComponent(q)}&limit=300`);
  const body=$('prod-body');$('prod-count').textContent=`共 ${res.count} 条`;
  if(!res.products.length){body.innerHTML='<tr><td colspan="5" class="empty">无商品，先选择站点</td></tr>';return}
  body.innerHTML=res.products.map(p=>`<tr>
    <td>${p.image?`<img src="${esc(p.image)}">`:''}</td>
    <td><a href="${esc(p.url)}" target="_blank">${esc(p.title)}</a><br><small style="color:var(--muted)">${esc(p.handle)}</small></td>
    <td>${p.price_min!=null?(p.price_min===p.price_max?p.price_min:`${p.price_min} - ${p.price_max}`):'-'}</td>
    <td>${esc(p.published)}</td>
    <td><a href="${esc(p.url)}" target="_blank">打开</a></td>
  </tr>`).join('');}
async function exportCsv(){const site=$('prod-site').value;if(!site){toast('先选择站点');return}window.open('/api/export?site='+encodeURIComponent(site)+'&format=csv')}
async function exportJson(){const site=$('prod-site').value;if(!site){toast('先选择站点');return}window.open('/api/export?site='+encodeURIComponent(site)+'&format=json')}
async function loadEvents(){
  const site=$('event-site').value;
  const res=await api('/api/events?site='+encodeURIComponent(site)+'&limit=80');
  const body=$('event-body');
  if(!res.events.length){body.innerHTML='<tr><td colspan="4" class="empty">暂无事件</td></tr>';return}
  body.innerHTML=res.events.map(e=>`<tr>
    <td>${esc((e.created_at||'').replace('T',' ').slice(0,19))}</td>
    <td>${esc(e.site_id)}</td>
    <td><span class="badge ${e.event_type==='new_product'?'ok':e.event_type.includes('error')?'failed':'off'}">${esc(e.event_type)}</span></td>
    <td>${esc(e.title||'')}</td>
  </tr>`).join('');}
async function loadFeishu(){
  const res=await api('/api/feishu');
  if(res.configured){$('fw-url').value=res.webhook_hint.replace('…','');$('fw-url').setAttribute('placeholder','已配置，输入新值可覆盖');}
}
async function saveFeishu(){
  const body={webhook_url:$('fw-url').value.trim(),secret:$('fw-secret').value.trim()};
  const res=await api('/api/feishu',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});
  if(res.ok){toast('飞书配置已保存');loadStatus()}}
async function testFeishu(){
  const res=await api('/api/feishu/test',{method:'POST'});
  toast(res.ok?'✅ 测试消息已发送':'❌ '+(res.error||'失败'));}
$('prod-site').addEventListener('change',loadProducts);
$('prod-q').addEventListener('keydown',e=>{if(e.key==='Enter')loadProducts()});
loadStatus();loadFeishu();
</script>
</body>
</html>
"""


def start_web(config_path: str = "config.yaml") -> None:
    run_web(config_path)
