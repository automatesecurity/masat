import os

from utils.history import default_db_path


def test_default_db_path_has_no_side_effects(tmp_path, monkeypatch):
    # If default_db_path created ~/.masat eagerly, this would touch HOME.
    monkeypatch.setenv("HOME", str(tmp_path))
    p = default_db_path()
    assert p.endswith(os.path.join(".masat", "masat.db"))
    assert not (tmp_path / ".masat").exists()
