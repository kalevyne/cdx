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
* **Hosting**: not yet decided — AWS (existing CalSol familiarity) and Berkeley-campus/CDA-provided infrastructure are both on the table.

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

Architecture finalized (Rev. 2, 06/29/2026) — single Box-native access control model; the earlier dual-paradigm Web3 experiment was abandoned. Stack decided (React + FastAPI + Box + XRPL). Next concrete step: designing the Box folder structure the dashboard will own (see `docs/PROJECT-SUMMARY.md`). No Box API access or XRPL wallet set up yet — that's the first unblock for Phase 1.

## Docs

* `CLAUDE.md` — context and conventions for AI-assisted development in this repo
* `docs/ARCHITECTURE.md` — technical architecture
* `docs/PROJECT-SUMMARY.md` — one-page project summary
* `docs/DECISIONS.md` — architecture decision log

## Sponsor

Built with support from Ripple's Center for Digital Assets (CDA).
