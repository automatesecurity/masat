import pytest

from scanners import nuclei_scanner


def test_has_nuclei_is_bool():
    assert isinstance(nuclei_scanner._has_nuclei(), bool)


@pytest.mark.asyncio
async def test_scan_returns_install_message_when_missing(monkeypatch):
    monkeypatch.setattr(nuclei_scanner, "_has_nuclei", lambda: False)
    res = await nuclei_scanner.scan("https://example.com")
    assert "Nuclei" in res
    assert "nuclei not installed" in res["Nuclei"]
