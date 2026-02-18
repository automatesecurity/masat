from utils.targets import parse_target


def test_parse_target_url_invalid_port_does_not_crash():
    info = parse_target("http://example.com:abc")
    assert info.kind == "url"
    assert info.host == "example.com"
    assert info.port is None


def test_parse_target_url_out_of_range_port_does_not_crash():
    info = parse_target("https://example.com:99999")
    assert info.kind == "url"
    assert info.host == "example.com"
    assert info.port is None
