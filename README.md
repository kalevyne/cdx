# CDX

Cross-subteam engineering documentation for CalSol, UC Berkeley's Solar Vehicle Team

CDX is a purpose-built engineering dashboard that gives CalSol's subteams visibility into each other's work — what's being built, where it stands in the design and review process, and a permanent, tamper-evident record of every file that gets committed.

Funded through Ripple's Center for Digital Assets (CDA).

## The problem

CalSol's subteams (battery, chassis, dynamics, electrical, shell, solar, strategy, bizops) work largely in isolation. There's no shared view of what other subteams are working on, what stage a component is at, or a durable history of engineering decisions that survives CalSol's high annual member turnover.

## The approach

CDX layers a dashboard on top of CalSol's existing Box Enterprise storage:

* Engineers upload files, write commit messages, attach design review documents, and browse the team's folder tree through the dashboard UI.
* Every commit is hashed (SHA-256) and the hash is anchored to XRPL mainnet via a `Memo` field — a permanent, infrastructure-independent record that a given file existed, unmodified, at a given time.
* Access control is Box-native (OAuth via CalSol's existing Box accounts) — no wallets, no separate login system.

The XRPL layer exists for permanence and independence from CalSol's own infrastructure — not decentralization for its own sake. Anchoring survives server migrations, lost credentials, and the team's yearly turnover in a way that a database record alone would not. It also supports the Ripple CDA sponsorship.

## Tech stack

* **Frontend**: React — folder tree browser, subsystem dashboard cards, upload/commit form. Click-to-explore CAD visualization is a nice-to-have, not core to v1 (see `docs/DECISIONS.md`).
* **Backend**: Python (FastAPI) — Box API calls, SHA-256 hashing, XRPL anchoring.
* **Storage & identity**: Box Enterprise — engineers authenticate with their existing Box/university account.
* **Ledger**: XRPL — commit hashes anchored via a `Memo` field. Testnet during development, mainnet at launch.
* **Database**: SQLite (dev) / Postgres (prod) — caches commit history and XRPL transaction references so the dashboard isn't querying XRPL on every page load.
* **Hosting**: Render for the demo (`render.yaml`, decision #9); the long-term target (AWS or Berkeley/CDA infrastructure) is still open.

## What's explicitly out of scope (v1)

These were considered and cut — see `docs/DECISIONS.md` for the reasoning:

* NFT / Web3-wallet-based access control (would require every engineer to hold and manage a crypto wallet — a fatal adoption barrier for a volunteer student team)
* IPFS
* Asset Administration Shell export
* "Master Vehicle NFT" concept
* Full CAD rendering/visualization (deferred past v1 — priority is Box + commit history + XRPL working solidly first)

## Architecture at a glance

```
Engineer → Dashboard UI (React) → Backend (FastAPI) → Box Enterprise (storage, OAuth)
                                                      → Hashing pipeline (SHA-256)
                                                          → XRPL (Memo field anchor)
                                                      → Postgres/SQLite (commit cache)
```

See `docs/ARCHITECTURE.md` for details.

## Implementation phases

1. Box API integration & data model — no blockchain code; fully testable on its own
2. Hashing pipeline & commit UI — still no blockchain code
3. XRPL anchoring & commit history view
4. Subsystem status dashboard & folder tree browser
5. Sponsor view, webhooks, and DAG

Phases 1–2 are deliberately sequenced before any XRPL work so team adoption can be validated before blockchain complexity is introduced.

## Status

Phases 1–4 are built, plus the lightweight sponsor view from Phase 5 (see `docs/DECISIONS.md` #9 for what was cut for the 2026-09-18 demo): Box OAuth login, a folder browser scoped to the Dashboard root, CDX commits (upload → Box → SHA-256 → database), background XRPL Testnet anchoring with a verification check, commit history, subsystem dashboard cards, and a public summary page. Box and XRPL behaviour is covered by tests against fakes; the live end-to-end checks still to run are listed in `docs/HANDOFF.md`.

## Docs

* `CLAUDE.md` — context and conventions for AI-assisted development in this repo
* `docs/HANDOFF.md` — checkpoint progress, open blockers, and what to check live next
* `docs/ARCHITECTURE.md` — technical architecture
* `docs/PROJECT-SUMMARY.md` — one-page project summary
* `docs/DECISIONS.md` — architecture decision log
* `docs/TIMELINE.md` — the checkpoint schedule for the demo deadline
* `docs/DEMO.md` — pre-demo checklist and the demo script
* `backend/README.md`, `frontend/README.md` — setup, layout, and commands

## Sponsor

Built with support from Ripple's Center for Digital Assets (CDA).
