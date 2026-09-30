"""Write the API's OpenAPI schema to frontend/src/api/openapi.json.

    python -m scripts.export_openapi && (cd ../frontend && npm run gen:api)

The frontend's TypeScript API types (frontend/src/api/schema.d.ts) are
generated from that file, so backend schemas stay the single source of truth.
tests/test_openapi_snapshot.py fails when the committed file is stale.
"""

import json
import os
from pathlib import Path

OPENAPI_PATH = Path(__file__).resolve().parents[2] / "frontend" / "src" / "api" / "openapi.json"

# The schema doesn't depend on real credentials; placeholders let this run anywhere.
for key in ("BOX_CLIENT_ID", "BOX_CLIENT_SECRET", "SESSION_SECRET"):
    os.environ.setdefault(key, "unused")


def render_openapi() -> str:
    from app.main import app

    return json.dumps(app.openapi(), indent=2, sort_keys=True) + "\n"


if __name__ == "__main__":
    OPENAPI_PATH.parent.mkdir(parents=True, exist_ok=True)
    OPENAPI_PATH.write_text(render_openapi())
    print(f"Wrote {OPENAPI_PATH}")
