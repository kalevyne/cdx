# CLAUDE.md

Context and conventions for AI-assisted development on CDX.

## What this project is

CDX is an engineering dashboard for CalSol (UC Berkeley's solar vehicle team) layered on top of their existing Box Enterprise storage. Engineers commit files through the dashboard UI; every commit's SHA-256 hash is anchored to XRPL for a permanent, tamper-evident record. See the root `README.md` for the full pitch and `docs/ARCHITECTURE.md` / `docs/PROJECT-SUMMARY.md` / `docs/DECISIONS.md` for depth.

Start with `docs/HANDOFF.md`: it tracks progress against `docs/TIMELINE.md`, what still needs a live check, and known blockers. Keep it current in the same commit as the work it describes.

## Repo layout

```
backend/    FastAPI app — Box client, login, CDX commits, XRPL anchoring, dashboard
frontend/   React app — dashboard, folder browser, commit form, history, sponsor page
docs/       Architecture, decisions, timeline, handoff, demo runbook
render.yaml Staging deploy (Render Blueprint)
```

`backend/README.md` and `frontend/README.md` map each directory; read them before adding a module.

## Backend (Python / FastAPI)

* Python 3.11+, type hints on all function signatures.
* Pydantic models for request/response schemas and internal data structures — don't pass around raw dicts across module boundaries.
* Formatting/linting: `ruff` (format + lint). Run before committing.
* Tests: `pytest`, colocated as `test_*.py` next to the module under test or under `backend/tests/` mirroring package structure.
* Box API and XRPL calls are backend-only. The frontend never talks to Box or XRPL directly — it goes through the FastAPI service, which holds the credentials.
* Secrets (Box service account credentials, XRPL wallet seed) come from environment variables / a secrets manager — never hardcoded, never committed. If you add a new required secret, document it in `backend/.env.example`.
* XRPL network is environment-driven (`XRPL_NETWORK=testnet|mainnet`), not hardcoded — development and CI must default to testnet.
* Routes stay thin; logic lives in `app/services/`. Services raise their own exceptions, and `app/errors.py` maps them to HTTP status codes — add new exception types there instead of try/except in routes.
* Every Box lookup by ID goes through `BoxService`, which rejects anything outside `BOX_DASHBOARD_ROOT_FOLDER_ID` (decision #11). Don't call box-sdk-gen directly from elsewhere.
* The list of subteams and the Box folder layout live only in `app/subsystems.py`.
* Schema changes need an Alembic migration (`alembic revision --autogenerate`); `tests/test_migrations.py` fails otherwise. Migrations run on startup.
* Tests fake Box and XRPL (`tests/conftest.py`: `box`, `fake_xrpl`, `client`); they never touch the network.

## Frontend (React)

* TypeScript, functional components, hooks. No class components.
* All HTTP goes through `frontend/src/api/`: components use the React Query hooks in `queries.ts`, never `fetch` directly.
* API types are generated from the backend's OpenAPI schema — never hand-write a type that mirrors a backend schema. After changing backend schemas/routes: `python -m scripts.export_openapi` (backend) then `npm run gen:api` (frontend); a backend test fails if the snapshot is stale.
* Shared UI states (empty/error/loading) come from `components/StateViews.tsx`; primitives live in `components/ui/`.
* CAD visualization is a nice-to-have deferred past v1 (see `docs/DECISIONS.md`) — don't build it out ahead of the folder tree / commit UI / dashboard cards that are actually in scope.

## Scope discipline

* Follow the phase sequencing in the README: Box integration + data model (Phase 1) and hashing pipeline + commit UI (Phase 2) come before any XRPL code (Phase 3). Don't reach for XRPL/blockchain code to solve a Phase 1–2 problem.
* Out-of-scope for v1, don't reintroduce without a decision recorded in `docs/DECISIONS.md`: NFT/wallet-based access control, IPFS, Asset Administration Shell export, "Master Vehicle NFT," full CAD rendering.
* Access control is Box OAuth only. Don't add a parallel auth system or wallet-based identity.

## Commit conventions

* Standard git conventions — imperative mood commit messages, one logical change per commit.
* Since this project uses SHA-256 + XRPL commit anchoring as its core feature, be precise in code about the distinction between a *git commit* (source code history) and a *CDX commit* (an engineer's file upload through the dashboard, hashed and anchored). Name variables/functions accordingly (e.g. `cdx_commit`, not bare `commit`) to avoid ambiguity.
