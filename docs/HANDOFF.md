# Handoff — checkpoint progress

Living progress log for working through the `docs/TIMELINE.md` checkpoints.
**If you are an agent picking this up, read this file first**, then continue
from the first unchecked item under "Checkpoint status". Update this file in
the same commit as the work it describes, so it never drifts from the code.

## Where the instructions came from

The task was "follow the prompts in `docs/checkpoint_prompts`", but that
directory does not exist on any branch (checked `main`,
`docs/scaffold-project-docs`, and PR #1 on 2026-09-30). The closest source
is the checkpoint list in `docs/TIMELINE.md`, so that is what this work
follows, item by item. **To fix later**: if `docs/checkpoint_prompts` exists
locally somewhere, push it and reconcile it against the status below.

## Branch

Work happens on `claude/checkpoint-prompts-dwlvyg`, which was fast-forwarded
onto `docs/scaffold-project-docs` (PR #1) because `main` only had a README.
If PR #1 merges first, this branch still merges cleanly on top of it.

## Resume in 60 seconds

```bash
# backend
cd backend && python3 -m venv .venv && . .venv/bin/activate
pip install -e ".[dev]"
pytest && ruff check . && ruff format --check .

# frontend
cd frontend && npm ci && npm run build && npm run lint
```

## Next steps for a human, in order

All code for Checkpoints 1–6 is written and tested against fakes. What's
left needs real accounts, credentials, or people:

1. **Local live run** (backend/README.md steps 1–7): add the second Box
   Redirect URI (`/api/auth/callback`), set `SESSION_SECRET`, delete any old
   `backend/cdx.db`, create a second faucet account for
   `XRPL_ANCHOR_DESTINATION`, then log in, create the folder layout, commit a
   file, and confirm the anchor on testnet.xrpl.org and "Verify now" goes
   green. This exercises every `[~]` item below in one sitting.
2. **Staging** (backend/README.md "Deploying to staging"): Render Blueprint,
   Box redirect URI for the deployed frontend, `box_oauth_setup` into the
   deployed DB. Check that the `/api/*` rewrite proxies (blocker 5 if not).
3. **Checkpoint 3's check**: a teammate who hasn't seen the code logs in,
   browses, and commits on staging.
4. **Demo prep** (docs/DEMO.md): seed data days ahead, subteam leads fill in
   their cards, backup video, custom domain, rehearsal.

## Environment limits hit (cloud agent sandbox)

The sandbox's network policy denies `api.box.com`, `s.altnet.rippletest.net`
and `faucet.altnet.rippletest.net`. Everything touching Box or XRPL is
therefore tested against mocks only. Every item marked **needs live check**
below still has to be run once against the real services by a human (or an
agent in an environment that allows those hosts).

## Checkpoint status

Legend: `[x]` done and tested · `[~]` code done, needs live check / human
action · `[ ]` not started · `[!]` blocked (see "Blocked / fix later").

### Day 0
- [x] Scaffolds, UI kit, XRPL Testnet wallet (done before this log started).
- [!] Domain + managed hosting accounts — needs a payment method (human).

### Checkpoint 1 — Backend + data model operational
- [x] Box API client wrapper (existed; router error handling moved to
  `app/errors.py`, folder listings raised to Box's 1000-item page size).
- [~] Dashboard root folder structure: `scripts/box_create_folder_structure.py`
  (layout defined once in `app/subsystems.py`). **Needs live run** against
  real Box: `python -m scripts.box_create_folder_structure "<Vehicle>"`.
- [x] `cdx_commits` migrations (Alembic, run automatically on startup) +
  psycopg driver. `tests/test_migrations.py` guards model/migration drift.
  [~] Managed Postgres instance itself not provisioned (needs an account).
- [~] Box OAuth login flow (`/api/auth/login|callback|me|logout`), tested
  with mocks. **Needs live check**: add
  `http://127.0.0.1:8000/api/auth/callback` as a second Redirect URI on the
  Box app, then follow backend/README.md step 5. Design: DECISIONS.md #11.

### Checkpoint 2 — Vertical slice deployed
- [x] SHA-256 hashing pipeline (`app/services/hashing.py`).
- [x] Commit endpoint `POST /api/cdx-commits`: upload → Box (new version if
  the name exists) → hash → `cdx_commits` row; subsystem derived from the
  Box folder path; optional design review goes to `<Subsystem>/Design
  Reviews`. The raw upload route was removed so nothing bypasses the record.
- [~] Staging deploy config: `render.yaml` now provisions Postgres, keeps the
  backend's Box token in the DB (`BOX_TOKEN_STORAGE=database`, since Render's
  disk is wiped per deploy), and proxies `/api/*` from the frontend domain.
  **Needs a human** to create the Render Blueprint and do the steps in
  backend/README.md "Deploying to staging". Unverified assumptions: Render
  static-site rewrites to an external URL work as a proxy, and the default
  `*.onrender.com` names are free (else update the 3 "SERVICE URL" lines).

### Checkpoint 3 — Core loop demoable
- [x] Commit form UI (`/commit`): folder picker, drag-and-drop file, message,
  optional design review, client-side validation, success card with SHA-256.
- [x] Folder tree browser (`/browse`): lazy tree that auto-expands to the
  selected folder, breadcrumbs, file downloads. Box access is scoped to the
  Dashboard root server-side (BoxService), so IDs outside it are 404.
- [x] Box OAuth login UI: login page with Box button + `login_error` messages;
  any 401 drops back to it.
- [x] Layout (app shell, Berkeley-blue theme, mobile nav), empty/loading/error
  states shared via `components/StateViews.tsx`.
- [~] **Needs live check**: walk a teammate through login → browse → commit
  on the deployed app (the checkpoint's own "Check"). Verified here only with
  a mocked API in headless Chromium at 1280px and 390px widths.
- Frontend API types are generated from the backend OpenAPI schema
  (frontend/README.md "API types"); a backend test catches staleness.

### Checkpoint 4 — XRPL anchoring live + commit history
- [~] XRPL client wrapper (`app/services/xrpl_client.py`): 1-drop Testnet
  `Payment` to `XRPL_ANCHOR_DESTINATION` with text memos (DECISIONS.md #12).
  Tested with mocks only. **Needs live check**: set
  `XRPL_TESTNET_WALLET_SEED` + `XRPL_ANCHOR_DESTINATION` (second faucet
  account, see backend/.env.example), commit a file, confirm the tx on
  testnet.xrpl.org shows the memos.
- [x] Async anchoring: background task after the commit response; status
  `pending → anchored | failed` (+ error, retry endpoint + button); pending
  commits swept on startup.
- [x] Verification: `GET /api/cdx-commits/{id}/verification` re-hashes the
  committed Box version and re-reads the ledger memo; the commit page's
  "Proof of record" panel shows file → SHA-256 → ledger with a "Verify now"
  button that marks each step matched/mismatched.
- [x] Commit history (`/history`) and commit detail (`/commits/:id`) views
  with live anchoring status and XRPL explorer links.

### Checkpoint 5 — Dashboard + subsystem cards + sponsor view
- [x] Subsystem metadata + status aggregation: `subsystem_metadata` table
  (owner, design stage concept → complete, note) + per-subsystem commit
  counts/last activity/recent commits (`GET/PATCH /api/subsystems`).
- [x] Dashboard (`/`): stat tiles, one card per subsystem with stage
  progress, lead, note, recent commits and inline editing; recent activity.
  History page gained subsystem filter chips; commit rows show a subsystem
  badge.
- [x] Sponsor view (`/sponsor`, no login, backed by `GET /api/public/summary`
  which omits author names/messages/Box IDs): hero, CDA credit, stats,
  subsystem stages, latest ledger proofs with explorer links, "how it works".
- [~] **Needs a human**: "real (not lorem-ipsum) copy" — the copy is written
  for CalSol but should be read by someone on the team; confirm the CDA
  credit wording with Ripple/CDA. Responsive layout checked at 390px and
  1280px with a mocked API only.

### Checkpoint 6 — Demo hardening
- [~] Demo seed data: `scripts/seed_demo_data.py` commits sample files for
  every subsystem through the real pipeline (Box → SHA-256 → XRPL), marks
  each file as sample data, never backdates, never invents leads
  (`--set-stages` fills unset stages only). Tested with fakes; **needs a live
  run** a few days before the demo (docs/DEMO.md).
- [x] Bug bash (fixes, each with a test where it's backend):
  - downloads of non-ASCII file names crashed with a 500 (Content-Disposition
    is now RFC 6266 with a UTF-8 `filename*`);
  - `?limit=` on the history API wasn't validated (0/negative meant "no
    limit" on SQLite);
  - "Anchoring…" spun forever when XRPL wasn't configured — new public
    `GET /api/status`; the UI shows "Not anchored yet" and stops polling;
  - deep links (e.g. a shared proof page) were lost across the Box login
    round trip — the page is now restored after login.
  - Full commit flow (validation → multipart upload → success card → badge
    flips to Anchored) exercised in headless Chromium against a mocked API.
- [x] Demo script + pre-demo checklist + fallbacks: `docs/DEMO.md`.
- [!] Backup demo video, custom domain, live rehearsal — human-only.

### After the checkpoints — file previews (2026-10-05)
- [x] In-app previews (DECISIONS.md #13): images, PDF, Markdown, CSV/TSV,
  text/code, from `/browse` (click a file; arrows step through the folder)
  and from a commit page (previews that commit's exact version). Unsupported
  or oversized files say so and offer the download.
- [x] Downloads/previews are streamed from Box instead of buffered, capped
  at `MAX_CONCURRENT_DOWNLOADS` (default 8) at once, and revalidated with
  ETags. Previews are refused over 20 MB server-side.
- [x] Downloaded files keep their real name: the name is also the last URL
  segment and the link's `download` attribute, for browsers/proxies that
  drop `Content-Disposition`.
- [~] **Needs live check**: verified in a browser against a faked Box only.
  Against real Box, open one of each type on `/browse`, and confirm a
  download saves under its own name (it was saving as "content" before; the
  header was already correct locally, so the cause wasn't reproduced).

## Blocked / fix later

Each entry: what's blocked, why, and the concrete next step.

1. **`docs/checkpoint_prompts` missing** — see "Where the instructions came
   from" above.
2. **No live Box/XRPL access from the agent sandbox** — see "Environment
   limits hit" above.
3. **Existing local `backend/cdx.db`** (created by the old `create_all`) will
   make the first Alembic migration fail with "table already exists". Delete
   it once; nothing wrote to it. Mentioned in backend/README.md step 3.
4. **New required setting `SESSION_SECRET`** — existing local `.env` files
   need it added or the backend won't start. render.yaml generates it.
5. **If Render's `/api/*` rewrite doesn't proxy to the backend** (item under
   Checkpoint 2): fallback is to point the frontend at the backend URL
   directly (`VITE_API_BASE_URL`), add CORS for `FRONTEND_URL` with
   credentials, and make the session cookie `SameSite=None`. Not built
   speculatively.
6. **shadcn registry blocked in the sandbox** — `src/components/ui/` primitives
   were hand-written in shadcn's style. Swap for CLI-generated versions
   (`npx shadcn@latest add card input textarea label badge skeleton alert`)
   when convenient; APIs are the same.
7. **Files over 50 MB** are rejected (Box's single-upload limit). CAD files
   can exceed that; supporting them means Box's chunked upload API in
   `BoxService.upload_file`. Uploads and the "Verify now" re-hash still read
   the whole file into memory; make both streaming at the same time.
8. **Direct edits in Box aren't prevented or recorded** — the original plan
   relied on a service account owning the tree, which decision #10 dropped.
   Committed versions stay verifiable (each CDX commit pins a Box version),
   but out-of-band edits are invisible to CDX. Next step: Box webhooks
   (Phase 5), or restricting the tree's collaborators in Box.
9. **Render free tier sleeps** after ~15 idle minutes (30–60 s cold start);
   the background anchoring task also dies with the instance, though pending
   commits are re-anchored on the next startup. Warm it before demos
   (docs/DEMO.md) or use a paid instance.
10. **Engineer permissions inside the dashboard tree** are the backend
    account's, not each engineer's (decision #11 trade-off). Revisit if
    subteams need private folders.

## Session log

- 2026-09-30 — Session 1: created this file, rebased branch onto PR #1's
  scaffold, confirmed 11 backend tests + frontend build pass as the baseline.
  Checkpoint 1 code done (30 backend tests). Checkpoint 2 code done (42).
  Checkpoint 3 done (45 backend tests; frontend build + lint clean).
  Checkpoint 4 done (60 backend tests). Checkpoint 5 done (67).
  Checkpoint 6 done (73 backend tests; frontend build + lint clean). Top-level
  docs (README, CLAUDE.md, ARCHITECTURE.md) refreshed to match the code.
- 2026-09-30 — Fix: `xrpl-py` was missing from `backend/pyproject.toml` (it
  was only installed in the agent's venv), so a fresh install crashed on
  startup with `No module named 'xrpl'`. Verified with a fresh venv built
  from `pyproject.toml` alone (73 tests pass).
