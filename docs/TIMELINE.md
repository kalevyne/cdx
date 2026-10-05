# Timeline — 2026-09-18 Deadline

18 days from kickoff (2026-08-31) to a hard external deadline (2026-09-18), starting from almost no code. This schedule breaks that into ~3-day checkpoints so slippage shows up early instead of on the last day. It compresses the phase plan in `docs/PROJECT-SUMMARY.md`/README and reflects the scope cuts and provisional defaults recorded in `docs/DECISIONS.md` #9.

**Priority for this deadline**: presentability slightly above full operational completeness — but functionality is not optional. The demo must show a real commit going through Box, getting hashed, and landing on XRPL Testnet, not a mockup. What gets cut is scope (Phase 5, full sponsor tooling, CAD), not correctness of what's built.

## Checkpoints

### Day 0 — Mon 2026-08-31 — Kickoff: unblock externals
These take calendar time, not just dev time, so they start immediately, in parallel with repo scaffolding:
- Request/register the Box service account + API app from CalSol's Box admin (blocks all Box work). **Status**: no service account; superseded by OAuth 2.0 User Authentication (`docs/DECISIONS.md` #10) — see `backend/README.md`.
- Create the XRPL Testnet wallet (free, instant). **Done (2026-09-08)** — funded via the public Testnet faucet, address `r3hDpqpYUWcFXsVfEenc5dPDCn2hMij3R2`, seed in `backend/.env` (gitignored, not committed).
- Buy a domain and stand up the managed-hosting accounts (see Budget below). **Open** — needs a payment method; not yet done.
- Scaffold `backend/` (FastAPI) and `frontend/` (React + a component library — see Budget) per `CLAUDE.md`. **Done** — both scaffolds exist and run.
- Pick and commit to a UI kit/theme now (e.g. shadcn/ui + Tailwind) so nothing needs a visual redo later — this is the cheapest presentability investment available and it's cheapest on day 0. **Done (2026-09-08)** — shadcn/ui + Tailwind v4 on the Vite scaffold, default neutral theme, no paid kit purchased.

### Checkpoint 1 — Thu 2026-09-03 — Backend + data model operational
- Box API client wrapper (auth, list folders, file metadata, upload/download).
- Dashboard root folder structure created in Box (per `docs/PROJECT-SUMMARY.md`).
- `cdx_commits` table + migrations on the managed Postgres instance.
- Box OAuth login flow working end-to-end (curl-testable, no UI yet).
- **Check**: can authenticate and list the real Box folder tree from the backend.

### Checkpoint 2 — Sun 2026-09-06 — Vertical slice deployed
- SHA-256 hashing pipeline.
- Commit endpoint: upload → Box → hash → `cdx_commits` row (XRPL fields still null).
- Backend deployed to staging (Railway/Render) — get real infra running now, not the week of the demo.
- Frontend scaffold deployed to Vercel with the chosen UI kit applied to a placeholder shell, so the staging URL already looks like the intended product.
- **Check**: a file can be committed through the API and shows up in Box and the DB, on the deployed staging environment.

### Checkpoint 3 — Wed 2026-09-09 — Core loop demoable
- Commit form UI (upload + message + optional design review attachment) wired to the backend.
- Read-only folder tree browser in the UI.
- Box OAuth login UI.
- First visual polish pass: consistent layout, empty states, loading states.
- **Check**: someone unfamiliar with the code can log in, browse the tree, and commit a file through the deployed UI. This is the compressed version of the "validate team adoption before adding ledger complexity" checkpoint from the phase plan — worth actually walking a teammate through it.

### Checkpoint 4 — Sat 2026-09-12 — XRPL anchoring live + commit history
- XRPL client wrapper (Testnet, `Payment` tx with `Memo`, per decision #9).
- Anchoring hooked into the commit flow (async, so the commit UI doesn't block on ledger confirmation).
- Verification endpoint/badge: re-fetch a commit's tx from XRPL and confirm the hash matches — this is the single best demo moment ("here's the file, here's its hash on a public ledger, here's proof they match") and deserves UI treatment, not just a log line.
- Commit history view: list commits, anchoring status (pending/confirmed), link to the XRPL Testnet explorer.
- **Check**: a commit made in the UI is visibly anchored and independently verifiable against the public ledger, without touching a terminal.

### Checkpoint 5 — Tue 2026-09-15 — Dashboard polish + subsystem cards + sponsor view
- Subsystem/subteam metadata + status aggregation.
- Dashboard cards per subsystem (status, recent commits, owner).
- Lightweight sponsor-facing summary view — this is the one to make look sharp given Ripple/CDA will likely see it; include their sponsorship credit.
- Dedicated visual-polish time: responsive layout check, consistent spacing/typography, real (not lorem-ipsum) copy.
- Explicitly not built for this deadline: webhooks, DAG, full sponsor tooling, CAD rendering (per decision #9).
- **Check**: the dashboard looks like a finished product to someone who has never seen the code, on a phone-width screen too.

### Checkpoint 6 — Thu 2026-09-17 — Demo hardening (day before deadline)
- Seed realistic demo data — multiple subsystems, a believable commit history — so nothing looks empty on stage.
- Bug bash: fix anything that would visibly break mid-demo; defer anything cosmetic that isn't visible in the demo path.
- Record a backup demo video/screen capture as insurance against live wifi/server failure.
- Confirm the custom domain resolves to production and the demo script/story is rehearsed at least once start-to-finish.
- **Check**: a full run-through, live, with no engineer narrating from the code.

### Fri 2026-09-18 — Deadline / presentation day
Buffer day. No new features — only fixes surfaced by the rehearsal.

## Budget — where money helps

None of these are required to hit a working demo, but each buys back days that are otherwise scarce. Ordered by when to spend:

| Item | Est. cost | Spend by | Why |
|---|---|---|---|
| Custom domain | ~$15–20/yr | Day 0 | DNS propagation takes time; cheap, immediate presentability win over a `*.vercel.app`/`*.railway.app` URL. |
| Managed hosting (Vercel + Railway/Render) | ~$20–50/mo | Day 0–Checkpoint 2 | Removes ops overhead entirely during the crunch; matches decision #9's "managed over self-hosted" call. Ask CalSol/CDA first — AWS credits (e.g. AWS Activate) or CDA-provided infra may cover this for free before spending out of pocket. |
| Managed Postgres (Neon/Supabase) | Free tier likely sufficient; ~$10–25/mo if reliability matters for demo day | Checkpoint 1 | Avoids self-hosting a DB under deadline pressure; paid tier removes cold-start delays if that matters for a live demo. |
| UI kit / component library license (e.g. a Tailwind UI / shadcn Pro block set) | ~$100–300 one-time | Day 0 | Buys a polished look immediately instead of hand-building components — directly serves the "presentability" priority and is cheaper than a design contractor with less coordination overhead in an 18-day window. |
| Icon/illustration pack for empty states and dashboard flourishes | ~$20–50 one-time | Checkpoint 3–5 | Small, cheap visual polish; skip if the UI kit above already covers it. |
| Error monitoring (Sentry free/starter tier) | Free–$26/mo | Checkpoint 2 | Cheap insurance against a silent failure mid-demo; not essential but low cost for the risk it removes. |

**Deliberately not recommending**: a freelance UI/UX contractor. A polished UI kit gets most of the same visual benefit without the onboarding/coordination time an unfamiliar freelancer costs in an 18-day window — revisit post-demo if there's a longer runway.

**Worth asking CDA/Ripple directly**: whether they can provide cloud credits or hosting before any of the above comes out of pocket — they were already mentioned as a possible infra source in `docs/PROJECT-SUMMARY.md`.
