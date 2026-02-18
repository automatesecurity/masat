from utils.targets import parse_target
from utils.workflows import plan_scans


def test_plan_for_url_includes_web():
    info = parse_target("https://example.com")
    plan = plan_scans(info)
    assert "web" in plan.scans


def test_plan_for_host_includes_nmap():
    info = parse_target("example.com")
    plan = plan_scans(info)
    assert "nmap" in plan.scans


def test_plan_for_cidr_includes_nmap_only():
    info = parse_target("10.0.0.0/24")
    plan = plan_scans(info)
    assert "nmap" in plan.scans
