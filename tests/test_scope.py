from utils.assets import ScopeConfig, in_scope


def test_scope_allows_subdomains():
    scope = ScopeConfig(allow_domains=["example.com"], allow_cidrs=[], deny_patterns=[])
    assert in_scope("https://a.example.com", scope)[0] is True
    assert in_scope("b.example.com", scope)[0] is True
    assert in_scope("example.com", scope)[0] is True


def test_scope_denies_by_pattern():
    scope = ScopeConfig(
        allow_domains=["example.com"],
        allow_cidrs=[],
        deny_patterns=["*admin*"],
    )
    assert in_scope("admin.example.com", scope)[0] is False


def test_scope_allows_ip_in_cidr():
    scope = ScopeConfig(allow_domains=[], allow_cidrs=["10.0.0.0/8"], deny_patterns=[])
    assert in_scope("10.1.2.3", scope)[0] is True
    assert in_scope("8.8.8.8", scope)[0] is False


def test_scope_allows_cidr_subset_only():
    scope = ScopeConfig(allow_domains=[], allow_cidrs=["10.0.0.0/8"], deny_patterns=[])
    assert in_scope("10.1.0.0/16", scope)[0] is True
    assert in_scope("0.0.0.0/0", scope)[0] is False
