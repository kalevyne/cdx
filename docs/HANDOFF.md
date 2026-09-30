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
- [ ] SHA-256 hashing pipeline.
- [ ] Commit endpoint: upload → Box → hash → `cdx_commits` row.
- [ ] Staging deploy config.

### Checkpoint 3 — Core loop demoable
- [ ] Commit form UI.
- [ ] Folder tree browser.
- [ ] Box OAuth login UI.
- [ ] Layout / empty / loading states.

### Checkpoint 4 — XRPL anchoring live + commit history
- [ ] XRPL client wrapper (Testnet `Payment` + `Memo`).
- [ ] Async anchoring in the commit flow.
- [ ] Verification endpoint + badge.
- [ ] Commit history view with explorer links.

### Checkpoint 5 — Dashboard + subsystem cards + sponsor view
- [ ] Subsystem metadata + status aggregation.
- [ ] Dashboard cards.
- [ ] Sponsor summary view.

### Checkpoint 6 — Demo hardening
- [ ] Demo seed data.
- [ ] Bug bash.
- [!] Backup demo video, custom domain, live rehearsal — human-only.

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

## Session log

- 2026-09-30 — Session 1: created this file, rebased branch onto PR #1's
  scaffold, confirmed 11 backend tests + frontend build pass as the baseline.
  Checkpoint 1 code done (30 backend tests).
