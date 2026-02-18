import os
import tempfile

from utils.history import default_db_path, list_runs, store_run


def test_default_db_path_endswith_db():
    assert default_db_path().endswith("masat.db")


def test_store_and_list_runs_roundtrip():
    with tempfile.TemporaryDirectory() as td:
        db = os.path.join(td, "t.db")
        run_id = store_run(db, "example.com", ["web"], {"x": 1}, [{"category": "c", "title": "t", "severity": 0, "remediation": "", "details": ""}])
        assert run_id > 0
        runs = list_runs(db)
        assert runs[0]["id"] == run_id
        assert runs[0]["target"] == "example.com"
