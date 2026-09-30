# CDX Backend

FastAPI service that reads and writes files in Box on behalf of the dashboard,
logs engineers in with Box OAuth, and owns the `cdx_commits` table.

Progress against `docs/TIMELINE.md` is tracked in `docs/HANDOFF.md`.

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
   - Under **Redirect URIs**, add both of these (they must exactly match
     `BOX_REDIRECT_URI` and `BOX_LOGIN_REDIRECT_URI` below):
     - `http://127.0.0.1:8000/api/box/oauth/callback` — the one-time backend
       authorization in step 4.
     - `http://127.0.0.1:8000/api/auth/callback` — engineers logging in to
       the dashboard.

     Use the literal IP `127.0.0.1`, not `localhost` — Box's redirect URI
     validation has been observed to silently reject `localhost` (the
     Configuration page returns a 200 but the value doesn't persist) while
     accepting `127.0.0.1`. For a deployment, add the deployed equivalents.
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
# fill in BOX_CLIENT_ID, BOX_CLIENT_SECRET, BOX_DASHBOARD_ROOT_FOLDER_ID, SESSION_SECRET
# everything else has working local defaults
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

The database schema is migrated to the latest version automatically on
startup (Alembic, see "Database migrations" below). If you have a `cdx.db`
from before migrations existed, delete it once — nothing wrote to it yet.

Visit `http://127.0.0.1:8000/docs` for interactive API docs, or
`http://127.0.0.1:8000/health` for a liveness check. Open the app at
`127.0.0.1`, not `localhost`: the login cookie is set for whichever host Box
redirects back to, and that has to be `127.0.0.1` (see step 1).

## 4. Create the Dashboard folder structure in Box (one-time)

```bash
python -m scripts.box_create_folder_structure "<Vehicle name>"
```

Creates `<Dashboard root>/<Vehicle>/<Subsystem>/{CAD, Design Reviews}` for
every subteam in `app/subsystems.py`. It's idempotent — re-run it after adding
a subsystem, or with another vehicle name for a new car.

## 5. Log in (curl-testable)

```bash
curl -i http://127.0.0.1:8000/api/auth/login   # 307 → Box consent URL
```

Open that `location` URL in a browser and approve. Box redirects to
`/api/auth/callback`, which checks that *your own* Box account can see the
Dashboard root folder, sets a signed `session` cookie, and redirects to
`FRONTEND_URL`. Then, with that cookie:

```bash
curl -b 'session=<value>' http://127.0.0.1:8000/api/auth/me
```

All `/api/folders`, `/api/files` and `/api/cdx-commits` routes return 401
without it. See
`docs/DECISIONS.md` #11 for why the login only identifies the engineer and
Box I/O still goes through the backend's own connection.

## 6. Make a CDX commit (curl-testable)

```bash
curl -b 'session=<value>' http://127.0.0.1:8000/api/cdx-commits \
  -F folder_id=<Box folder ID> -F message="Initial pack layout" \
  -F file=@pack.step -F design_review=@review.pdf   # design_review is optional
```

This uploads the file to that Box folder (as a new version if a file with the
same name is already there), computes its SHA-256, and records a
`cdx_commits` row. The subsystem is worked out from the folder's path (the
nearest ancestor named after an entry in `app/subsystems.py`), and the design
review goes into that subsystem's `Design Reviews` folder. Files are limited
to 50 MB (Box's single-upload limit).

## 7. XRPL anchoring

Set `XRPL_TESTNET_WALLET_SEED` and `XRPL_ANCHOR_DESTINATION` (see
`.env.example`). After each CDX commit is saved, a background task submits a
1-drop Testnet `Payment` whose memos carry the commit's data, then records the
transaction hash and ledger index on the row:

| MemoType                   | MemoData                          |
|----------------------------|-----------------------------------|
| `cdx/commit-id`            | the CDX commit's ID               |
| `cdx/sha256`               | SHA-256 of the committed file     |
| `cdx/design-review-sha256` | SHA-256 of the design review, if any |

Both are stored as hex-encoded UTF-8 text, so explorers show them readably.
`anchor_status` is `pending` → `anchored`, or `failed` with `anchor_error`
(retry with `POST /api/cdx-commits/{id}/anchor`). Commits left `pending` —
because XRPL wasn't configured yet, or the server restarted mid-anchor — are
anchored automatically on the next startup.

`GET /api/cdx-commits/{id}/verification` re-downloads the committed version
from Box and re-reads the memo from the ledger, and reports whether both
still match the recorded hash.

## Deploying to staging (Render)

`render.yaml` at the repo root is a Render Blueprint for both services plus a
Postgres database. After the first deploy:

1. Add `https://<frontend>.onrender.com/api/auth/callback` as a Redirect URI
   on the Box app, and fill in the `sync: false` env vars in Render.
2. Authorize the backend's Box connection into the deployed database, from
   your laptop:
   ```bash
   DATABASE_URL='<cdx-db external URL>' BOX_TOKEN_STORAGE=database \
     python -m scripts.box_oauth_setup
   ```
   (The local redirect URI still works — the token just lands in Postgres
   instead of a file, where the deployed backend reads it.)

## What's here

- `app/main.py` — app wiring: session middleware, error handlers, routers,
  migrations on startup.
- `app/config.py` — env-driven settings (`pydantic-settings`); see
  `.env.example` for the full list.
- `app/errors.py` — maps service exceptions (`BoxNotFoundError`, …) to HTTP
  status codes in one place, so routes don't repeat try/except blocks.
- `app/auth.py` — session helpers and the `require_user` dependency.
- `app/subsystems.py` — the single list of subteams and the Box folder layout.
- `app/services/box_client.py` — `BoxService`, a thin wrapper over
  [box-sdk-gen](https://github.com/box/box-python-sdk-gen) for list/read/upload/
  download, translating Box API errors into `BoxNotFoundError` / `BoxServiceError`.
- `app/services/box_login.py` — the engineer login exchange + access check.
- `app/services/box_token_storage.py` — file- or database-backed storage for
  the backend's own Box token.
- `app/services/hashing.py` — SHA-256 of committed file bytes.
- `app/services/cdx_commits.py` — creating/reading CDX commits.
- `app/services/xrpl_client.py` — submit/read XRPL memo transactions.
- `app/services/anchoring.py` — anchoring CDX commits + verification.
- `app/services/dashboard.py` — subsystem cards and the public summary.
- `app/routers/` — thin FastAPI routes over the services.
- `app/models/` — the `cdx_commits`, `subsystem_metadata` and `box_tokens` tables.
- `migrations/` — Alembic migrations for every table.
- `scripts/` — one-off operator commands (Box authorization, folder layout).

Uploads only happen through CDX commits: there's deliberately no raw upload
route, since a file written to the dashboard tree without a commit would have
no hash or record.

## Tests & linting

```bash
pytest
ruff check .
ruff format .
```

Box and XRPL calls are faked in tests (`tests/conftest.py`) — no live Box
account or ledger is needed to run the suite. Each test gets its own SQLite file, migrated the same way production is.

## Database migrations

Schema changes go through Alembic. After changing a model:

```bash
alembic revision --autogenerate -m "describe the change"
```

Review the generated file in `migrations/versions/`, then restart the app (or
run `alembic upgrade head`). `tests/test_migrations.py` fails if a model and
the migrations disagree, so a forgotten migration shows up in CI.

## API endpoints

| Method | Path                             | Auth | Purpose                                   |
|--------|----------------------------------|------|--------------------------------------------|
| GET    | `/health`                        | —    | Liveness check                            |
| GET    | `/api/auth/login`                | —    | Redirect to Box login                     |
| GET    | `/api/auth/callback`             | —    | Box redirects here; sets session cookie   |
| GET    | `/api/auth/me`                   | yes  | The logged-in engineer                    |
| POST   | `/api/auth/logout`               | —    | Clear the session                         |
| GET    | `/api/folders`                   | yes  | List the configured Dashboard root folder |
| GET    | `/api/folders/{folder_id}`       | yes  | List an arbitrary folder's contents       |
| GET    | `/api/files/{file_id}`           | yes  | File metadata                             |
| GET    | `/api/files/{file_id}/content`   | yes  | Download file bytes                       |
| POST   | `/api/cdx-commits`               | yes  | Commit a file (multipart, see step 6)     |
| GET    | `/api/cdx-commits`               | yes  | Recent CDX commits (`?subsystem=&limit=`) |
| GET    | `/api/cdx-commits/{id}`          | yes  | One CDX commit                            |
| POST   | `/api/cdx-commits/{id}/anchor`   | yes  | Retry anchoring a pending/failed commit   |
| GET    | `/api/cdx-commits/{id}/verification` | yes | Re-check hash against Box + ledger    |
| GET    | `/api/subsystems`                | yes  | Dashboard cards: stage, lead, activity    |
| PATCH  | `/api/subsystems/{slug}`         | yes  | Update lead / stage / note                |
| GET    | `/api/public/summary`            | —    | Sponsor view: totals, stages, proofs      |
