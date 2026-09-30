# CDX Backend

Phase 1: Box API integration & data model. FastAPI service that reads and writes
files in Box on behalf of the dashboard, plus the `cdx_commits` table schema that
Phase 2 (hashing pipeline + commit UI) will start writing to.

No blockchain code here — see `docs/DECISIONS.md` and the root `README.md` for
phase sequencing.

## 1. Set up Box access (one-time, do this first)

**Current approach: OAuth 2.0 User Authentication, not a service account.**
CDX originally planned a Client Credentials Grant (CCG) service account (see
`docs/ARCHITECTURE.md`), but that requires an Enterprise-tier Box account to
register, and Berkeley IT rejected the request outright over API costs —
see `docs/DECISIONS.md` #10. OAuth 2.0 Custom Apps don't have that
restriction: they can be created on a completely free, non-enterprise Box
account, because an unpublished custom app doesn't need enterprise approval.

The trade-off: instead of an independent service-account identity, the
backend acts *as whichever Box account completes the one-time authorization
below*. Point that at your own Berkeley Box account and CDX inherits
whatever CalSol folders that account can already see — no separate
folder-sharing step needed. The real cost is that this ties the backend's
Box access to one person's account rather than a durable service identity;
revisit this once Box access isn't blocking anything (ask CalSol/IT again,
or pursue the nonprofit donation route via TechSoup) — don't let it become
permanent by default.

1. Sign up for a free Box account (any email — this does **not** need to be
   your Berkeley account, and does **not** need to be Enterprise-tier).
2. Go to the [Box Developer Console](https://app.box.com/developers/console)
   logged into that free account. **Create Platform App** → **Custom App**
   → **User Authentication (OAuth 2.0)**. Name it `CDX Dashboard`.
3. Under **Configuration**:
   - Note the **Client ID** and **Client Secret**.
   - Under **Redirect URIs**, add `http://127.0.0.1:8000/api/box/oauth/callback`
     (must exactly match `BOX_REDIRECT_URI` below). Use the literal IP
     `127.0.0.1`, not `localhost` — Box's redirect URI validation has been
     observed to silently reject `localhost` (the Configuration page returns
     a 200 but the value doesn't persist) while accepting `127.0.0.1`.
   - Under **Application Scopes**, enable at least "Read and write all files
     and folders stored in Box."
4. Fill in `.env` (see step 2 below) with the Client ID/Secret, then run:
   ```bash
   python -m scripts.box_oauth_setup
   ```
   This opens the Box consent screen in your browser — **log in with your
   Berkeley Box account** (the one with real access to CalSol's folders) and
   approve access. The script catches the redirect locally and saves a token
   to `BOX_TOKEN_STORAGE_PATH` (gitignored); it refreshes itself
   automatically after that, and you shouldn't need to re-run this unless
   the token file is lost or access is revoked.
5. Note the Dashboard root folder's ID from its Box URL, e.g.
   `https://calsol.app.box.com/folder/123456789` → `123456789`.

## 2. Configure environment

```bash
cp .env.example .env
# fill in BOX_CLIENT_ID, BOX_CLIENT_SECRET, BOX_DASHBOARD_ROOT_FOLDER_ID
# BOX_REDIRECT_URI and BOX_TOKEN_STORAGE_PATH already have working defaults
```

`.env` is gitignored — never commit real credentials (see `CLAUDE.md`). The
OAuth token file (`BOX_TOKEN_STORAGE_PATH`, default `.box_tokens`) is also
gitignored — it's as sensitive as a password, since it grants access to
whatever Box account authorized it.

## 3. Run locally

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

uvicorn app.main:app --reload
```

Visit `http://localhost:8000/docs` for interactive API docs, or
`http://localhost:8000/health` for a liveness check.

## 4. What's here

- `app/services/box_client.py` — `BoxService`, a thin wrapper over
  [box-sdk-gen](https://github.com/box/box-python-sdk-gen) for list/read/upload/
  download, translating Box API errors into `BoxNotFoundError` / `BoxServiceError`.
- `app/routers/files.py` — FastAPI routes exposing that: browse folders, fetch file
  metadata, download file content, upload a file into a folder.
- `app/models/cdx_commit.py` — the `cdx_commits` table from the architecture sketch.
  Defined now so the schema exists, but nothing writes to it yet — that starts in
  Phase 2 once the hashing pipeline exists to fill in `sha256_hash`.
- `app/config.py` — env-driven settings (`pydantic-settings`); see `.env.example`
  for the full list.
- `scripts/box_oauth_setup.py` — one-time OAuth authorization, see step 1 above.

## 5. Tests & linting

```bash
pytest
ruff check .
ruff format .
```

Box API calls are mocked in tests (`tests/test_box_client.py`,
`tests/test_files_router.py`) — no live Box account is needed to run the suite.

## API endpoints (Phase 1 scope)

| Method | Path                          | Purpose                                   |
|--------|-------------------------------|--------------------------------------------|
| GET    | `/api/folders`                | List the configured Dashboard root folder |
| GET    | `/api/folders/{folder_id}`    | List an arbitrary folder's contents       |
| GET    | `/api/files/{file_id}`        | File metadata                             |
| GET    | `/api/files/{file_id}/content`| Download file bytes                       |
| POST   | `/api/folders/{folder_id}/files` | Upload a file into a folder            |

Commit messages, hashing, and the commit history view are Phase 2 — these routes
are the raw Box I/O layer they'll be built on top of.
