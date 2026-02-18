import pytest

from scanners.subdomain_scanner import extract_domain, normalize_crtsh_names


def test_extract_domain_from_url():
    assert extract_domain("https://example.com/path") == "example.com"


def test_extract_domain_from_host_port():
    assert extract_domain("example.com:8443") == "example.com"


def test_normalize_crtsh_names_splits_and_strips_wildcards():
    names = normalize_crtsh_names("*.a.example.com\nb.EXAMPLE.com\n\n")
    assert names == ["a.example.com", "b.example.com"]
