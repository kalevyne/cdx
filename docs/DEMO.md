# Demo runbook

The story to rehearse for `docs/TIMELINE.md` Checkpoint 6: a real file goes
through Box, gets hashed, lands on XRPL Testnet, and is verified — live, with
no engineer narrating from the code. ~6 minutes.

## A few days before

- [ ] Staging is deployed and both Redirect URIs are on the Box app
      (`backend/README.md`, "Deploying to staging").
- [ ] `https://<frontend>/api/status` returns `"anchoring_enabled": true`.
      If not, set `XRPL_TESTNET_WALLET_SEED` and `XRPL_ANCHOR_DESTINATION` and
      redeploy — pending commits are anchored automatically on startup.
- [ ] Seed history so nothing looks empty (real uploads, real anchors; files
      are marked as sample data in their first line):
      ```bash
      python -m scripts.seed_demo_data "<Vehicle name>" --set-stages
      ```
      Run it days ahead, not minutes: timestamps are real and the dashboard
      shows "last commit" times. Real commits from the team beat seed data.
- [ ] Ask each subteam lead to set their lead name, stage and note on their
      dashboard card (the seed never invents leads).
- [ ] Record the backup video of the full script below.

## Day of, one hour before

- [ ] Open `https://<frontend>/health` via the frontend and backend URLs.
      Render's free tier sleeps after ~15 idle minutes and takes 30–60 s to
      wake — do this again five minutes before going on.
- [ ] Log in as the presenter; have a teammate's login ready too.
- [ ] Testnet faucet balance on the anchoring wallet is non-zero (each
      anchor costs 1 drop + the fee; the faucet gives plenty).
- [ ] Have two small files on the desktop: the one to commit, and a design
      review PDF.
- [ ] Open the backup video in a background tab.

## Script

1. **The problem (30 s)** — open `/sponsor`. "CalSol's subteams work largely
   in isolation, and the team turns over every year. CDX is one shared view
   of everyone's work, with a record that outlives any one class."
2. **Log in (20 s)** — "Team login" → "Log in with Box". Engineers use the
   Berkeley Box accounts they already have; no wallets, no new passwords.
3. **Dashboard (60 s)** — every subsystem's stage, lead, and latest files.
   Click a recent commit on the Battery card.
4. **Browse (30 s)** — Browse → <Vehicle> → Solar → CAD. "This is CalSol's real
   Box, read-only here — changes go through commits."
5. **Commit live (60 s)** — "Commit a file here" → drop the file, write a
   one-line message, attach the design review → "Commit to Box". Point out
   the SHA-256 on the success card.
6. **Anchoring (20 s)** — the badge flips from "Anchoring…" to "Anchored"
   in a few seconds. "That's a transaction on the public XRP Ledger."
7. **Proof (90 s)** — "View proof" → the three steps. Click **Verify now**:
   CDX re-downloads the file from Box, re-hashes it, re-reads the ledger, and
   both steps turn green. Click the ledger link → the explorer shows the same
   hash in the `cdx/sha256` memo. Optional: `shasum -a 256 <file>` in a
   terminal shows the same 64 characters.
8. **Why it matters (30 s)** — "If anyone edits that file in Box, or even
   our database, verification fails — and the ledger copy can't be changed.
   It survives server migrations, lost credentials, and graduating classes."
9. **Close on `/sponsor` (20 s)** — totals, stages, latest proofs, and the
   CDA credit.

## If something breaks

| Symptom | Fallback |
|---|---|
| Page takes 30+ s to load | Render cold start — wait, or switch to the video. |
| Login fails | Use the teammate's login, or narrate from `/sponsor` (no login). |
| Commit stays "Anchoring…" | Show an already-anchored seed commit's proof instead; the anchor usually lands on the next ledger. |
| "Not anchored yet" badge | XRPL isn't configured on the server — see "A few days before". |
| Box or wifi down | Play the backup video. |
