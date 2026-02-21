from utils.schema import normalize_findings


def test_normalize_findings_includes_asset_and_scanner():
    results = {
        "Web Checks": {
            "Header missing": {"severity": 5, "remediation": "Add header", "details": "x"}
        }
    }
    findings = [f.to_dict() for f in normalize_findings(results, asset="example.com")]
    assert findings and findings[0]["asset"] == "example.com"
    assert findings[0]["scanner"] == "Web Checks"
    assert "confidence" in findings[0]
    assert "references" in findings[0]
