from utils.report_templates import RunForReport, run_to_markdown


def test_report_markdown_contains_summary():
    run = RunForReport(
        id=1,
        ts=1700000000,
        target="https://example.com",
        scans=["web"],
        results={},
        findings=[
            {"category": "c", "title": "t", "severity": 7, "details": "d", "remediation": "r"},
            {"category": "c", "title": "t2", "severity": 3, "details": "", "remediation": ""},
        ],
    )
    md = run_to_markdown(run)
    assert "MASAT Report" in md
    assert "Target:" in md
    assert "Findings:" in md
    assert "Top findings" in md
    assert "Findings (detailed)" in md
