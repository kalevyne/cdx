# CDX — Project Summary (Rev. 2, 2026-06-29)

## Purpose & context

Calvin is a member of CalSol, UC Berkeley's solar vehicle team, building a blockchain-anchored engineering documentation system funded through Ripple's Center for Digital Assets (CDA). The core problem is cross-subteam visibility — engineers don't know what other subteams are working on or where they are in the design and build process. The system anchors SHA-256 file hashes to XRPL mainnet as a permanent record layer, with the honest technical justification being immutability of records across high-turnover student generations, independent of CalSol's own infrastructure. The XRPL component also serves the Ripple sponsorship relationship.

## Current state

The architecture went through a significant revision. The major shift was abandoning a dual-paradigm access control experiment (NFT/Web3 wallet approach via an XRPL EVM Sidechain, alongside Box-native OAuth) in favor of a single Box-native access control approach — driven by the recognition that a Web3 wallet requirement would undermine team adoption. Also cut from v1 scope: IPFS, Asset Administration Shell export, and the "Master Vehicle NFT" concept. Full CAD rendering/visualization was also deferred past v1 as a nice-to-have, not core to the initial build.

The architecture is a purpose-built engineering dashboard layered on top of CalSol's existing Box Enterprise storage. Engineers upload files, write commit messages, attach design review documents, and browse folder trees through the dashboard UI; the backend silently anchors SHA-256 hashes to XRPL via Memo fields.

**Stack**: React frontend, FastAPI backend, Box Enterprise for storage/identity, XRPL for anchoring, Postgres/SQLite for a commit-history cache. Hosting is undecided (AWS or Berkeley/CDA infrastructure).

## Implementation phases

1. Box API integration and data model — no blockchain code; fully testable on its own
2. Hashing pipeline and commit UI — still no blockchain code
3. XRPL anchoring and commit history view
4. Subsystem status dashboard and folder tree browser
5. Sponsor view, webhooks, and DAG

No hard sponsor deadline exists yet, but phases are deliberately sequenced for implementation order regardless of dates: Phases 1–2 validate team adoption before any blockchain complexity is introduced.

## On the horizon

The immediate next concrete step is designing the Box folder structure the dashboard will own — a dedicated Dashboard root folder, per-vehicle and per-subsystem subfolders, CAD and Design Reviews subdirectories, with service-account-enforced write restrictions so engineers interact with files only through the dashboard UI rather than Box directly.

Neither Box API access nor an XRPL wallet is set up yet — both are prerequisites before Phase 1 and Phase 3 implementation, respectively, can start for real.

## Key learnings & principles

* Phases 1 and 2 are fully testable without any XRPL code, allowing team adoption to be validated before blockchain complexity is introduced — a deliberate sequencing insight.
* Access control decisions should be driven by realistic team adoption constraints, not technical elegance; requiring Web3 wallets would have been a fatal friction point.
* The XRPL layer's honest value proposition is permanence and independence from CalSol's infrastructure, not decentralization for its own sake — being clear-eyed about this shapes what belongs in v1.
* Scope discipline matters for a volunteer, high-turnover team: CAD visualization, richer Web3 features, and infra decisions are deferred rather than guessed at, so early phases stay shippable.

## Tools & resources

* Storage & identity: Box Enterprise (existing CalSol infrastructure)
* Frontend: React
* Backend: Python (FastAPI)
* Database: SQLite (dev) / Postgres (prod)
* Blockchain: XRPL (Memo fields for hash anchoring; testnet in dev, mainnet at launch)
* Sponsor/funder: Ripple's Center for Digital Assets (CDA)
* Hosting: undecided — AWS or Berkeley-campus/CDA infrastructure
