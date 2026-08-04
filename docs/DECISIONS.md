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
