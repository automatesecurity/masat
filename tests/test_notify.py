from utils.notify import should_notify


def test_notify_triggers_on_added_ports():
    diff = {"exposure": {"added_ports": ["443/tcp https"]}, "new_findings": []}
    d = should_notify(diff)
    assert d.should_notify


def test_notify_triggers_on_new_high_findings():
    diff = {"exposure": {}, "new_findings": [{"severity": 9}]}
    d = should_notify(diff, high_sev_threshold=8)
    assert d.should_notify


def test_notify_skips_when_no_change():
    diff = {"exposure": {"added_ports": [], "removed_ports": []}, "new_findings": []}
    d = should_notify(diff)
    assert d.should_notify is False
