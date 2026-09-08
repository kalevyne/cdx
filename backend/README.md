# CDX Backend

Phase 1: Box API integration & data model. FastAPI service that reads and writes
files in Box on behalf of the dashboard, plus the `cdx_commits` table schema that
Phase 2 (hashing pipeline + commit UI) will start writing to.

No blockchain code here — see `docs/DECISIONS.md` and the root `README.md` for
phase sequencing.

## 1. Set up the Box service account (one-time, do this first)

The backend talks to Box as a dedicated **service account**, authenticated with
Box's Client Credentials Grant (CCG) — this is the "service-account-authenticated"
client described in `docs/ARCHITECTURE.md`. It's separate from engineers' own Box
logins; engineer identity/OAuth login is a later concern (Phase 4 area), not needed
to read/write files today.

Box service accounts don't automatically see your enterprise's existing files —
they start with their own empty root folder, exactly like a new teammate would. You
have to explicitly share the CDX Dashboard root folder with the service account's
email, the same way you'd invite a collaborator in the Box web UI. This is the key
fact that makes the self-serve path below possible: the app can be registered
under *any* enterprise, and the resulting service account is just an email address
that gets invited into a CalSol folder like any other collaborator — regardless of
which enterprise created it.

There are two paths to get the four values you need (Client ID, Client Secret,
Enterprise ID, Dashboard folder ID). Try Path A first — it doesn't need anyone's
help.

### Path A — self-serve, using your own enterprise account (try this first)

If you have your own Enterprise-tier Box account (e.g. via campus IT, a
different org, or a paid plan — not the free personal tier), you can do this
entirely yourself:

1. Go to the [Box Developer Console](https://app.box.com/developers/console)
   logged into **your own** enterprise account (not CalSol's).
2. **Create Platform App** → **Custom App** → **Server Authentication (Client
   Credentials Grant)**. Give it a name like `CDX Dashboard`.
3. Under **Configuration**:
   - Note the **Client ID** and **Client Secret**.
   - Under "App + Enterprise Access", note the **Service Account ID** and the
     service account's email, something like
     `AutomationUser_123456_xyz@boxdevedition.com`.
   - Under **Application Scopes**, enable `Read and write all files and folders
     stored in Box`.
   - From your own enterprise's Admin Console → **Enterprise Settings**, note
     your **Enterprise ID**.
4. Confirm you can actually generate a token. If app creation succeeds but
   requesting a token errors with something like "not approved for use," your
   own enterprise restricts custom apps (Admin Console → Apps → Custom App
   Approval) — you're blocked here, not on CalSol's side. Skip to Path B.
5. Log into your **own regular CalSol account** in the Box web app, open the
   Dashboard root folder (see `docs/PROJECT-SUMMARY.md` for the intended
   structure), and invite the service account's email as an **Editor**
   collaborator. Editor-level members can normally invite new collaborators, so
   this may not need anyone else at all — Box will show an "external
   collaborator" warning since the email is outside CalSol's domain, which is
   expected, not an error.
6. If that invite fails because CalSol restricts external collaborators
   ("Restrict collaboration to within your enterprise" on the folder or
   enterprise settings), you need someone with Editor+ rights on that specific
   folder — not full account access — to either send the invite themselves or
   temporarily allow external collaboration.

If Path A works, you're done without needing the CalSol account owner at all.

### Path B — ask a CalSol admin (fallback if Path A is blocked)

The app is registered under CalSol's own enterprise instead, done by whoever
administers the `calsol` Box account:

1. Go to the [Box Developer Console](https://app.box.com/developers/console) while
   logged into the CalSol Box account.
2. **Create Platform App** → **Custom App** → **Server Authentication (Client
   Credentials Grant)**. Give it a name like `CDX Dashboard`.
3. Under **Configuration**:
   - Note the **Client ID** and **Client Secret**.
   - Under "App + Enterprise Access", note the **Service Account ID** — the
     console also shows the service account's email, something like
     `AutomationUser_123456_xyz@boxdevedition.com`.
   - Under **Application Scopes**, enable `Read and write all files and folders
     stored in Box` (Manage Users is not needed — CDX doesn't do user provisioning).
4. If the CalSol enterprise restricts custom apps (Admin Console → **Apps** →
   **Custom App Approval**), approve this app's Client ID there — this needs
   actual **Enterprise Admin/Co-Admin** rights, which is a different, enterprise-
   wide role from folder-level "Co-owner." If you're the only admin and apps
   aren't restricted, you can skip this.
5. In the regular Box web app, create (or pick) the **Dashboard root folder** and
   **share it** with the service account's email as an **Editor**. This is what
   actually grants the backend access; the Custom App creation step alone does not.
6. From CalSol's Admin Console → **Enterprise Settings**, note the **Enterprise
   ID**.

Either path ends with the same four values: Client ID, Client Secret, Enterprise
ID, and the Dashboard root folder's ID (visible in its Box URL, e.g.
`https://calsol.app.box.com/folder/123456789` → `123456789`). The app code
doesn't care which path produced them.

## 2. Configure environment

```bash
cp .env.example .env
# fill in BOX_CLIENT_ID, BOX_CLIENT_SECRET, BOX_ENTERPRISE_ID, BOX_DASHBOARD_ROOT_FOLDER_ID
```

`.env` is gitignored — never commit real credentials (see `CLAUDE.md`).

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
