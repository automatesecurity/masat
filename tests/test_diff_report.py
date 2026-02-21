from utils.diff_report import diff_to_markdown
from utils.diffing import DiffResult


def test_diff_report_markdown_contains_sections():
    d = DiffResult(
        target="t",
        old_run_id=1,
        new_run_id=2,
        new_findings=[{"severity": 8, "title": "x", "category": "c"}],
        resolved_findings=[],
        exposure={"added_ports": ["443/tcp https"], "removed_ports": [], "server_header": {"old": "a", "new": "b"}},
    )
    md = diff_to_markdown(d)
    assert "Exposure changes" in md
    assert "Added ports" in md
    assert "Findings changes" in md
