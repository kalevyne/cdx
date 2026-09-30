# Architecture Decision Log

Chronological record of significant decisions for CDX, including what was considered and cut. Newest at the bottom.

---

## 1. Box-native access control over dual NFT/Web3-wallet paradigm

**Decision**: Access control is Box OAuth only — engineers log in with their existing CalSol/university Box account. No wallet-based identity or NFT-gated access.

**Considered**: An earlier design paired Box-native auth with a parallel NFT/Web3-wallet access model on an XRPL EVM Sidechain.

**Why rejected**: Requiring every engineer to hold and manage a crypto wallet is a fatal adoption barrier for a volunteer student team with high annual turnover. Realistic adoption constraints outweigh technical elegance here.

---

## 2. IPFS excluded from v1

**Decision**: Files live in Box only; no IPFS pinning/mirroring layer.

**Why rejected**: Adds operational complexity (pinning, availability) without a problem it solves that Box + XRPL anchoring don't already cover for this use case.

---

## 3. Asset Administration Shell (AAS) export excluded from v1

**Decision**: No AAS export in v1.

**Why rejected**: Out of scope for the core problem (cross-subteam visibility + durable record); revisit only if a concrete downstream consumer needs it.

---

## 4. "Master Vehicle NFT" concept dropped

**Decision**: No NFT represents the vehicle or its components.

**Why rejected**: A Web3-native framing that doesn't map to a real need — CDX's honest value proposition is permanence/independence via hash anchoring, not asset representation or ownership semantics.

---

## 5. CAD visualization deferred past v1

**Decision**: The Phase 4 folder tree browser ships with file icons/metadata, not interactive CAD rendering. Click-to-explore CAD (select parts/systems, see who owns them) is a nice-to-have for a later phase.

**Why**: Priority is getting Box integration, the commit workflow, and XRPL anchoring solid first — that's the core value proposition. CAD visualization is valuable for team usability but isn't required to solve the stated problem (cross-subteam visibility + durable record) and would add significant scope (format support, rendering) before the fundamentals are proven.

**Status**: Confirmed for v1 scope (2026-08-04).

---

## 6. XRPL network strategy: testnet in dev, mainnet at launch

**Decision**: Development and CI anchor to XRPL Testnet. Production anchoring switches to mainnet once the system is trusted enough for real records.

**Why**: Avoids real XRP costs and mainnet noise during iteration while keeping the anchoring code path identical (network selected via `XRPL_NETWORK` env var) so the switch at launch is a config change, not a rewrite.

**Open**: Who custodies the signing wallet (a CalSol officer, a CDA-provided account, a project secrets manager) is not yet decided. Must be resolved before Phase 3 implementation goes beyond testnet, and definitely before any mainnet anchoring.

**Status**: Tentative (2026-08-04) — network strategy agreed, wallet custody still open.

---

## 7. Hosting/deployment target — open

**Decision**: Not yet made.

**Candidates**: AWS (CalSol has existing familiarity), or Berkeley-campus/CDA-provided infrastructure.

**Why open**: No pressure to decide yet since Phases 1–2 don't require a production deployment target. Backend should stay twelve-factor (config via env vars) so the eventual choice doesn't require rework.

**Status**: Open (2026-08-04) — revisit before Phase 3–4 deployment planning.

---

## 8. XRPL transaction type for anchoring — open

**Decision**: Not yet made.

**Candidates**: A minimal-value `Payment` transaction, or an `AccountSet` transaction (no value transfer) — both support a `Memo` field.

**Why open**: Doesn't block Phase 1–2 work; needs to be settled before Phase 3 (XRPL anchoring) implementation starts.

**Status**: Open (2026-08-04).

---

## 9. Scope compression and provisional defaults for the 2026-09-18 demo deadline

**Decision**: A hard external deadline of 2026-09-18 was set with almost no code yet written. For that deadline only, presentability is weighted slightly above full operational completeness — this does not mean faking functionality; real Box integration, hashing, and XRPL testnet anchoring must actually work, just that visual polish and a working demo narrative get equal or greater priority than round out every feature.

**Cut/deferred past the demo**: Phase 5 (webhooks, DAG visualization) is deferred past 2026-09-18. The demo's sponsor-facing view is a lightweight read-only summary page, not the full sponsor feature set envisioned for later. Full CAD visualization stays deferred per decision #5.

**Provisional defaults to unblock #6/#7/#8 for the demo** (time-boxed choices, not final production decisions):

* **XRPL transaction type (#8)**: use a `Payment` transaction with a minimal amount. Most legible to a non-technical audience ("this is a real transaction on the public ledger") and the simplest to implement under time pressure.
* **Wallet custody (#6)**: a project-controlled XRPL Testnet wallet for the demo. Mainnet launch and its custody question remain open and are explicitly out of scope for 2026-09-18.
* **Hosting (#7)**: managed platforms (e.g. Vercel for the frontend, Railway/Render for the backend, a managed Postgres such as Neon/Supabase) rather than self-managed AWS or campus infrastructure, to avoid spending scarce days on ops. AWS/Berkeley/CDA infrastructure stays the candidate for the long-term target after the demo.

**Why**: With an 18-day runway and no existing code, every day spent deliberating is a day not spent building. These defaults were chosen for being cheap, reversible, and fast to stand up — not necessarily the eventual production choice. See `docs/TIMELINE.md` for the checkpoint schedule and budget this scope maps to.

**Status**: Provisional, scoped to the 2026-09-18 deadline (2026-08-31). Long-term mainnet custody and hosting decisions remain open per #6/#7.

---

## 10. Box auth: OAuth 2.0 User Authentication instead of a CCG service account

**Decision**: The backend authenticates to Box via OAuth 2.0 (User Authentication), acting as whichever Box account completes a one-time authorization (`backend/scripts/box_oauth_setup.py`), instead of an independent Client Credentials Grant (CCG) service account.

**Considered**: The original plan (`docs/ARCHITECTURE.md`) was a CCG service account, registered under some Enterprise-tier Box account and invited as a collaborator into CalSol's folders — either Berkeley's own enterprise or a separate paid one, per `backend/README.md`'s original Path A/B.

**Why rejected**: Berkeley IT rejected the API app request outright, citing Box API costs, and paying out of pocket for a separate Business-tier account (~$15-20/mo) wasn't viable either. OAuth 2.0 Custom Apps sidestep both: an unpublished custom app doesn't need enterprise approval, so it can be registered on a completely free, non-enterprise Box account.

**Trade-off accepted**: The backend no longer has an independent service-account identity — it acts as whatever specific Box account (intended: the maintainer's own Berkeley account) authorized it, inheriting that account's own folder access instead of needing an explicit collaborator invite. This is weaker than a service account: it's tied to one person's continued access, not a durable team-owned identity. Revisit once Box access stops being a blocker (retry Berkeley IT, or pursue Box's nonprofit donation program via TechSoup if CalSol or a fiscal sponsor qualifies as a 501(c)(3)) — don't let this stopgap become permanent by default.

**Status**: Active (2026-09-28). Superseding decision — the CCG approach described in `docs/ARCHITECTURE.md` is no longer current; that doc should be updated to match when next touched.
