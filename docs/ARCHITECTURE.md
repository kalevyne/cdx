# Architecture

## Overview

CDX is a dashboard layered on top of CalSol's existing Box Enterprise storage. It does not replace Box as the file store — it adds a commit workflow, cross-subteam visibility, and a tamper-evident record on top of it.

```
Engineer
  │
  ▼
Dashboard UI (React)
  │  upload file, write commit message, browse folder tree, view subsystem status
  ▼
Backend (FastAPI)
  │
  ├─► Box Enterprise API — file storage, OAuth identity, folder tree
  │
  ├─► Hashing pipeline — SHA-256 of uploaded file content
  │
  ├─► XRPL — anchor hash in a Memo field (testnet in dev, mainnet at launch)
  │
  └─► Postgres/SQLite — commit history cache (Box file ref, hash, XRPL tx ref, author, message, timestamp)
```

## Components

### Dashboard UI (React)

* Folder tree browser mirroring the Box folder structure the dashboard owns.
* Commit form: file upload + commit message + optional design review document attachment.
* Subsystem status dashboard: per-subteam/per-component cards showing current state.
* Commit history view: shows past commits with links to the anchoring XRPL transaction.
* Talks only to the FastAPI backend — never calls Box or XRPL directly, so credentials never reach the browser.

### Backend (FastAPI)

* Box API client — authenticated via OAuth 2.0 as one authorized Box account (decision #10, which replaced the original service-account plan), handles upload, folder listing, and file metadata, and refuses anything outside the Dashboard root.
* Engineer login — Box OAuth identifies the engineer and checks their own account can see the Dashboard root; Box I/O then uses the backend's connection (decision #11).
* Hashing pipeline — computes SHA-256 over file bytes at commit time.
* XRPL anchoring — submits the hash as a `Memo` on an XRPL transaction (see "Open question: transaction type" below).
* Commit cache DB — every CDX commit's metadata is written to Postgres/SQLite immediately; the XRPL transaction hash/ledger index is attached once anchoring confirms. This means the dashboard's commit history view reads from the cache, not from XRPL directly, keeping page loads fast and decoupled from ledger availability.

### Box Enterprise

* Owns actual file storage and provides OAuth-based identity — engineers log in with their existing CalSol/university Box account.
* A dedicated **Dashboard root folder** (see `docs/PROJECT-SUMMARY.md` for the intended structure) is the only tree the dashboard manages. Engineers are meant to write through the dashboard so every change is hashed and anchored. That isn't enforced in Box yet: with OAuth instead of a service account (#10) there's no separate identity to own the tree, so direct edits in Box are possible and simply aren't recorded. Each CDX commit pins a Box file version, so verification still checks the exact committed bytes; detecting out-of-band edits (Box webhooks) is Phase 5 work.

### XRPL

* Used purely as an anchoring/timestamping layer, not for identity, access control, or asset representation.
* Each CDX commit's SHA-256 hash goes into a transaction `Memo` field. The transaction hash + ledger index are stored in the commit cache DB alongside the CDX commit record, so any commit can be independently verified against the public ledger later.
* **Transaction type**: a 1-drop `Payment` to a second project-controlled account, with `cdx/commit-id`, `cdx/sha256` and `cdx/design-review-sha256` text memos (decisions #9 and #12; provisional for the Testnet demo).
* **Open question — wallet custody**: who holds the signing key for the anchoring account (a CalSol officer, a CDA-provided account, a project-specific secret manager) is not yet decided. Must be resolved before any mainnet anchoring goes live.
* **Network strategy**: testnet during development (Phases 1–4), mainnet at launch. Driven by an `XRPL_NETWORK` environment variable, never hardcoded.

## Data model

Defined in `backend/app/models/` with Alembic migrations in `backend/migrations/`:

* `cdx_commits` — Box file ID + version + folder, file name/size, SHA-256, optional design review (Box ID + SHA-256), subsystem, author (Box user ID + name), message, anchoring status/error, XRPL network + tx hash + ledger index, created/anchored timestamps.
* `subsystem_metadata` — per-subsystem lead, design stage, and note (which subsystems exist is defined in `backend/app/subsystems.py`).
* `box_tokens` — the backend's Box OAuth token when `BOX_TOKEN_STORAGE=database`.

## Deployment

For the demo, managed hosting on Render (`render.yaml`: backend web service, static frontend with an `/api` proxy, Postgres) per decision #9. The long-term target (AWS or Berkeley/CDA infrastructure) is still open (#7); the backend stays twelve-factor (config via environment variables) so it isn't locked into one host.
