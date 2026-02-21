import os
import tempfile

from utils.history import store_run, get_run, list_runs_for_target
from utils.diffing import diff_exposure, diff_findings


def test_diff_findings_added_and_resolved():
    old = [
        {"asset": "t", "category": "c", "title": "a"},
        {"asset": "t", "category": "c", "title": "b"},
    ]
    new = [
        {"asset": "t", "category": "c", "title": "b"},
        {"asset": "t", "category": "c", "title": "d"},
    ]

    added, resolved = diff_findings(old, new)
    assert [f["title"] for f in added] == ["d"]
    assert [f["title"] for f in resolved] == ["a"]


def test_exposure_diff_ports_and_server_header():
    old_results = {
        "Nmap Scan": {
            "\nOpen Ports": {
                "details": "Port  Service  Version\n----  -------  -------\n22/tcp  ssh  OpenSSH\n80/tcp  http  Apache\n"
            }
        },
        "Web Server Technology": {
            "Detected Server": {"details": "Server header: Apache"}
        },
    }
    new_results = {
        "Nmap Scan": {
            "\nOpen Ports": {
                "details": "Port  Service  Version\n----  -------  -------\n22/tcp  ssh  OpenSSH\n443/tcp  https  nginx\n"
            }
        },
        "Web Server Technology": {
            "Detected Server": {"details": "Server header: nginx"}
        },
    }

    exposure = diff_exposure(old_results, new_results)
    assert "80/tcp http" in exposure["removed_ports"]
    assert "443/tcp https" in exposure["added_ports"]
    assert exposure["server_header"]["old"] == "Apache"
    assert exposure["server_header"]["new"] == "nginx"


def test_history_get_run_and_list_runs_for_target():
    with tempfile.TemporaryDirectory() as td:
        db_path = os.path.join(td, "masat.db")
        store_run(db_path, "example.com", ["web"], {"r": 1}, [{"asset": "example.com", "category": "c", "title": "a"}])
        store_run(db_path, "example.com", ["web"], {"r": 2}, [{"asset": "example.com", "category": "c", "title": "b"}])

        runs = list_runs_for_target(db_path, "example.com", limit=10)
        assert len(runs) == 2

        run = get_run(db_path, runs[0]["id"])
        assert run and run["target"] == "example.com"
        assert run["results"]
        assert run["findings"]
