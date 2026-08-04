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

* Box API client — service-account-authenticated, handles upload, folder listing, and file metadata.
* Hashing pipeline — computes SHA-256 over file bytes at commit time.
* XRPL anchoring — submits the hash as a `Memo` on an XRPL transaction (see "Open question: transaction type" below).
* Commit cache DB — every CDX commit's metadata is written to Postgres/SQLite immediately; the XRPL transaction hash/ledger index is attached once anchoring confirms. This means the dashboard's commit history view reads from the cache, not from XRPL directly, keeping page loads fast and decoupled from ledger availability.

### Box Enterprise

* Owns actual file storage and provides OAuth-based identity — engineers log in with their existing CalSol/university Box account.
* A dedicated **Dashboard root folder** (see `docs/PROJECT-SUMMARY.md` for the intended structure) is the only tree the dashboard manages. A Box service account enforces that engineers write through the dashboard UI rather than editing that tree directly in Box — direct edits would bypass hashing/anchoring and break the commit record.

### XRPL

* Used purely as an anchoring/timestamping layer, not for identity, access control, or asset representation.
* Each CDX commit's SHA-256 hash goes into a transaction `Memo` field. The transaction hash + ledger index are stored in the commit cache DB alongside the CDX commit record, so any commit can be independently verified against the public ledger later.
* **Open question — transaction type**: candidates are a low-cost `Payment` (e.g. to self, minimal XRP amount) or an `AccountSet` (no value transfer). Needs a decision before Phase 3; record it in `docs/DECISIONS.md` once made.
* **Open question — wallet custody**: who holds the signing key for the anchoring account (a CalSol officer, a CDA-provided account, a project-specific secret manager) is not yet decided. Must be resolved before any mainnet anchoring goes live.
* **Network strategy**: testnet during development (Phases 1–4), mainnet at launch. Driven by an `XRPL_NETWORK` environment variable, never hardcoded.

## Data model (sketch)

Commit cache, roughly:

```
cdx_commits
  id
  box_file_id
  box_file_version
  subsystem / subteam
  author (Box identity)
  message
  sha256_hash
  xrpl_tx_hash        (nullable until anchored)
  xrpl_ledger_index   (nullable until anchored)
  created_at
  anchored_at         (nullable)
```

This will firm up during Phase 1 (Box API integration & data model).

## Deployment (open)

Not yet decided. AWS is plausible given CalSol's existing familiarity; Berkeley-campus or CDA-provided infrastructure is also on the table. No architectural decisions should assume a specific host until this is settled — keep the backend twelve-factor (config via environment variables) so it isn't locked into one target.
