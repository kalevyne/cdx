from scripts.export_openapi import OPENAPI_PATH, render_openapi


def test_frontend_openapi_snapshot_is_current():
    """The frontend's API types are generated from this snapshot. If this fails:
    python -m scripts.export_openapi && (cd ../frontend && npm run gen:api)"""
    assert OPENAPI_PATH.read_text() == render_openapi()
