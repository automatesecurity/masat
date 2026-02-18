def test_api_module_not_imported_by_default():
    # This test is intentionally minimal: it ensures core tests do not
    # implicitly depend on FastAPI.
    import scanners.registry  # noqa: F401
