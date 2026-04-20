# compliance-collector-portal

Next.js 14 portal UI for the compliance-collector backend (v0.5).

## What it does

* Lets a Global Admin sign in with their Microsoft 365 account (MSAL.js).
* Presents a framework selector — tick CIS M365, SOC 2, etc.
* Fires **POST /assessments** on the backend to queue a run.
* Polls `/assessments/{id}` every 3s and shows live status.
* When the run completes, calls `/assessments/{id}/report/summary` and
  renders KPI cards + a findings table. The full HTML report opens in a
  new tab.

## Local development

```powershell
# From the repo root
cd portal
copy .env.example .env.local    # PowerShell: Copy-Item .env.example .env.local
npm install
npm run dev
```

Portal is up at <http://localhost:3000>. Make sure the backend is also
running on <http://localhost:8080>.

### Dev bypass

`.env.local` ships with `NEXT_PUBLIC_DEV_BYPASS_AUTH=true`. In this mode:

* The portal skips MSAL entirely — no Entra app registration required.
* The backend receives unauthenticated requests and injects a fake
  Global Admin principal (only when `ENVIRONMENT=dev`).

This lets you iterate on the UI without touching Entra. Flip both flags
off in staging/prod.

## Scripts

| Command | Purpose |
|---|---|
| `npm run dev` | Dev server with HMR |
| `npm run build && npm start` | Production build |
| `npm run lint` | ESLint (Next.js core-web-vitals config) |
| `npm run typecheck` | `tsc --noEmit` |
| `npm test` | Vitest unit tests |

## Project layout

```
portal/
├── src/
│   ├── app/
│   │   ├── layout.tsx              ← root layout, NavBar, AuthProvider
│   │   ├── page.tsx                ← marketing landing
│   │   ├── assessments/
│   │   │   ├── page.tsx            ← list view, SWR-polled
│   │   │   ├── new/page.tsx       ← framework selector + Start button
│   │   │   └── [id]/page.tsx       ← status polling + results
│   │   └── auth/callback/page.tsx  ← MSAL redirect landing
│   ├── components/
│   │   ├── AuthProvider.tsx        ← wraps MsalProvider (or bypass)
│   │   ├── NavBar.tsx
│   │   └── StatusPill.tsx
│   └── lib/
│       ├── msalConfig.ts           ← PublicClientApplication config
│       ├── api.ts                  ← typed fetch helper w/ bearer tokens
│       └── types.ts                ← shared TS types + FRAMEWORKS catalog
├── next.config.mjs                 ← /api/backend/* → FastAPI rewrite
├── tailwind.config.ts
├── tsconfig.json
└── package.json
```

## Deploying (later)

Planned v0.6 target: Azure Static Web Apps (free tier) fronted by the
same Entra app as the backend. Until then, `npm start` behind any host
that can reach the backend is fine.
