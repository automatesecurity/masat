import os
import tempfile

import pytest

from utils.history import store_run


def test_store_run_does_not_create_arbitrary_parent_dirs(tmp_path):
    # If the parent directory doesn't exist and it's not the default MASAT dir,
    # we should not auto-create it.
    missing_parent = tmp_path / "does-not-exist"
    db_path = missing_parent / "x.db"

    with pytest.raises(Exception):
        store_run(str(db_path), "t", ["web"], {"x": 1}, [])

    assert not missing_parent.exists()
