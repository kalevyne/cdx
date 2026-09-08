# CDX Frontend

Phase 1 scaffold: Vite + React + TypeScript, Tailwind CSS v4, shadcn/ui (locked in
per `docs/TIMELINE.md` Day 0 — no paid UI kit). No app components yet; this is the
toolchain the folder tree / dashboard cards / commit UI will be built on.

## Run locally

```bash
npm install
npm run dev
```

## Adding components

```bash
npx shadcn@latest add <component>
```

Installed components land in `src/components/ui/`. Keep Box/XRPL data-fetching out
of components — see `frontend/src/api/` convention in the root `CLAUDE.md`.
