import os
from pathlib import Path

from monitor.config import data_dir, parse_config


def test_data_dir_uses_home_when_no_config(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)  # 无 config.yaml 的目录
    d = data_dir()
    assert "monitor-agent" in str(d)


def test_data_dir_uses_cwd_when_config_exists(monkeypatch, tmp_path):
    (tmp_path / "config.yaml").write_text("sites: []\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    assert str(data_dir()) == str(Path.cwd().resolve())


def test_data_dir_env_override(monkeypatch, tmp_path):
    monkeypatch.setenv("MONITOR_AGENT_DIR", str(tmp_path / "custom"))
    assert str(data_dir()).startswith(str((tmp_path / "custom").resolve()))


def test_parse_config_resolves_relative_paths_to_data_dir(monkeypatch, tmp_path):
    monkeypatch.setenv("MONITOR_AGENT_DIR", str(tmp_path / "agent"))
    cfg = parse_config({"sites": [], "storage": {"path": "./data/monitor.db"}, "export": {"dir": "./exports"}})
    assert str(cfg.storage.path).startswith(str((tmp_path / "agent").resolve()))
    assert str(cfg.export.dir).startswith(str((tmp_path / "agent").resolve()))


def test_parse_config_keeps_absolute_paths(monkeypatch, tmp_path):
    monkeypatch.setenv("MONITOR_AGENT_DIR", str(tmp_path / "agent"))
    cfg = parse_config({"sites": [], "storage": {"path": "/var/db/monitor.db"}, "export": {"dir": "/tmp/out"}})
    assert cfg.storage.path == "/var/db/monitor.db"
    assert cfg.export.dir == "/tmp/out"