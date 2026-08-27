from monitor.config import init_config, DEFAULT_CONFIG_YAML, load_config
import yaml


def _write_cfg(tmp_path, sites, feishu=""):
    cfg = {"sites": sites}
    if feishu:
        cfg["feishu"] = {"webhook_url": feishu}
    p = tmp_path / "config.yaml"
    p.write_text(yaml.safe_dump(cfg, allow_unicode=True), encoding="utf-8")
    return p


def test_init_config_creates_full_template_on_first_run(tmp_path):
    p = tmp_path / "config.yaml"
    init_config(p)
    d = yaml.safe_load(p.read_text(encoding="utf-8"))
    template = yaml.safe_load(DEFAULT_CONFIG_YAML)
    assert len(d["sites"]) == len(template["sites"])  # 31 站


def test_init_config_merges_preset_sites_into_existing(tmp_path):
    # 用户已有自定义站点 + example
    p = _write_cfg(
        tmp_path,
        [
            {"id": "my-custom-site", "name": "My", "base_url": "https://a.com", "adapter": "shopify_products_json"},
        ],
        feishu="https://open.feishu.cn/open-apis/bot/v2/hook/myhook",
    )
    init_config(p)
    d = yaml.safe_load(p.read_text(encoding="utf-8"))
    ids = [s["id"] for s in d["sites"]]
    assert "my-custom-site" in ids  # 用户自己的保留
    assert "viqzes" in ids          # 预设站点被合并进来
    template = yaml.safe_load(DEFAULT_CONFIG_YAML)
    assert len(ids) == 1 + len(template["sites"])
    # webhook 不被覆盖
    assert d["feishu"]["webhook_url"] == "https://open.feishu.cn/open-apis/bot/v2/hook/myhook"


def test_init_config_merge_is_idempotent(tmp_path):
    p = tmp_path / "config.yaml"
    init_config(p)
    init_config(p)  # 再跑一次
    d = yaml.safe_load(p.read_text(encoding="utf-8"))
    template = yaml.safe_load(DEFAULT_CONFIG_YAML)
    assert len(d["sites"]) == len(template["sites"])  # 不重复添加