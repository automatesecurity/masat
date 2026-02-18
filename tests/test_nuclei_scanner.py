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


@pytest.mark.asyncio
async def test_scan_reports_failure_when_subprocess_fails(monkeypatch):
    monkeypatch.setattr(nuclei_scanner, "_has_nuclei", lambda: True)

    class DummyProc:
        returncode = 2

        async def communicate(self):
            return b"", b"boom"

    async def dummy_create(*args, **kwargs):
        return DummyProc()

    monkeypatch.setattr(nuclei_scanner.asyncio, "create_subprocess_exec", dummy_create)
    res = await nuclei_scanner.scan("https://example.com")
    assert "nuclei execution failed" in res["Nuclei"]


@pytest.mark.asyncio
async def test_scan_overall_severity_is_max_of_findings(monkeypatch):
    monkeypatch.setattr(nuclei_scanner, "_has_nuclei", lambda: True)

    class DummyProc:
        returncode = 0

        async def communicate(self):
            # Two findings: low and critical
            low = {"info": {"name": "A", "severity": "low"}, "matched-at": "x", "template": "t1"}
            crit = {"info": {"name": "B", "severity": "critical"}, "matched-at": "y", "template": "t2"}
            return (f"{__import__('json').dumps(low)}\n{__import__('json').dumps(crit)}\n").encode(), b""

    async def dummy_create(*args, **kwargs):
        return DummyProc()

    monkeypatch.setattr(nuclei_scanner.asyncio, "create_subprocess_exec", dummy_create)
    res = await nuclei_scanner.scan("https://example.com")
    assert res["Nuclei"]["Nuclei findings"]["severity"] == 10
