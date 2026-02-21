import asyncio

from utils.expand import _normalize_hostname, expand_domain


def test_normalize_hostname_basic():
    assert _normalize_hostname("Example.COM") == "example.com"
    assert _normalize_hostname("*.Example.COM") == "example.com"
    assert _normalize_hostname("example.com.") == "example.com"
    assert _normalize_hostname("") is None


def test_expand_domain_resolve_off_includes_input():
    assets = asyncio.run(expand_domain("example.com", use_crtsh=False, resolve=False, max_hosts=10))
    assert len(assets) == 1
    assert assets[0].hostname == "example.com"
    assert assets[0].ips == []
    assert assets[0].source == "input"
