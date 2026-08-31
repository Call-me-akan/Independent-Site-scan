from monitor.updater import _version_gt


def test_version_compare():
    assert _version_gt("0.7.0", "0.6.3") is True
    assert _version_gt("1.0.0", "0.9.9") is True
    assert _version_gt("0.6.3", "0.6.3") is False
    assert _version_gt("0.6.2", "0.6.3") is False
    assert _version_gt("0.6.10", "0.6.9") is True


def test_version_compare_pre_release():
    # 0.6.4-rc1 < 0.6.4
    assert _version_gt("0.6.4", "0.6.4-rc1") is True