from monitor.state import ControlState


def test_control_state_default_enabled(tmp_path):
    ctrl = ControlState(tmp_path / "daemon.state")
    assert ctrl.read("enabled", True) is True  # 默认开启


def test_control_state_toggle(tmp_path):
    ctrl = ControlState(tmp_path / "daemon.state")
    ctrl.write("enabled", False)
    assert ctrl.read("enabled", True) is False
    ctrl.write("enabled", True)
    assert ctrl.read("enabled", True) is True


def test_control_state_corrupt(tmp_path):
    p = tmp_path / "daemon.state"
    p.write_text("not-json", encoding="utf-8")
    ctrl = ControlState(p)
    assert ctrl.read("enabled", True) is True  # 损坏文件回退默认