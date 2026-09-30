# CDX Frontend

Vite + React + TypeScript, Tailwind CSS v4, shadcn/ui-style components (locked
in per `docs/TIMELINE.md` Day 0 — no paid UI kit). Progress is tracked in
`docs/HANDOFF.md`.

## Run locally

```bash
npm install
npm run dev        # http://127.0.0.1:5173 — use 127.0.0.1, not localhost
```

The dev server proxies `/api` to the backend on `127.0.0.1:8000` (start it
per `backend/README.md`), so the app and API share an origin and the Box login
cookie just works. `render.yaml` does the same with a rewrite in staging.

## Layout

```
src/
  api/          the only code that talks HTTP
    client.ts     fetch wrapper (ApiError), login/download URLs
    queries.ts    React Query hooks + query keys — components use these
    types.ts      friendly names for the generated API types
    schema.d.ts   GENERATED from the backend's OpenAPI schema (don't edit)
    openapi.json  GENERATED snapshot the types come from (don't edit)
  components/   shared building blocks (app shell, folder tree, states, …)
    ui/           shadcn-style primitives (button, card, input, …)
  pages/        one component per route (see App.tsx)
  lib/          formatting + class-name helpers
```

## API types

Types for requests/responses are generated from the backend, never written by
hand. After changing a backend schema or route:

```bash
(cd ../backend && python -m scripts.export_openapi)
npm run gen:api
```

The backend test suite fails if `openapi.json` is stale.

## Adding components

The shadcn CLI (`npx shadcn@latest add <component>`) needs network access to
ui.shadcn.com. The primitives in `src/components/ui/` were hand-written in the
same style when that wasn't available; prefer the CLI when it is.

## Checks

```bash
npm run build   # typecheck + production build
npm run lint
```
