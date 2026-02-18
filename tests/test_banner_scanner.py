from scanners.banner_scanner import parse_target


def test_parse_target_url():
    host, scheme, port = parse_target("https://example.com:8443/path")
    assert host == "example.com"
    assert scheme == "https"
    assert port == 8443


def test_parse_target_host_port():
    host, scheme, port = parse_target("example.com:443")
    assert host == "example.com"
    assert scheme is None
    assert port == 443
