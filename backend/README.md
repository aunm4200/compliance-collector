# compliance-collector-backend

FastAPI backend for the **compliance-collector** portal (v0.4 preview of v1.0 GA).

It exposes:

| Path | Purpose |
|---|---|
| `GET /healthz` / `/readyz` | Liveness / readiness probes |
| `GET /auth/me` | Returns the authenticated principal (from the portal JWT) |
| `GET /consent/url` | Builds a tenant-scoped admin-consent URL |
| `POST /consent/callback` | Records the result of the admin-consent redirect |
| `GET /consent/status` | Consent state for the caller's tenant |
| `POST /assessments` | Queues a new assessment run (Global Admin only) |
| `GET /assessments` | Lists the caller tenant's assessments |
| `GET /assessments/{id}` | Single assessment status |
| `GET /assessments/{id}/report/summary` | JSON summary for a completed run |
| `GET /assessments/{id}/report/html` | HTML report for a completed run |

---

## Architecture highlights

* **Cert-free Graph auth.** `graph_auth.py` selects between three modes via
  `GRAPH_AUTH_MODE`:
  * `mi_fic` *(production)* — user-assigned Managed Identity mints a token
    for `api://AzureADTokenExchange`; that token is used as a client
    assertion against our multi-tenant Entra app in the customer tenant.
    **No secrets, no certificates.**
  * `secret` *(dev only)* — client secret from env.
  * `cert` *(legacy)* — PEM certificate, matches the v0.3 CLI.
* **Tenant isolation.** Every read/write is scoped to the caller's `tid`
  claim. Assessments can never be fetched across tenants.
* **Admin-only writes.** `POST /assessments` requires the
  `GlobalAdministrator` app role (granted during admin consent).
* **Structured logs.** Every request gets an `x-request-id` correlation
  ID, bound into structlog context.
* **Pluggable storage.** `LocalStorage` today; Azure Blob Storage with
  managed identity in v0.5.

---

## Local development

```bash
# From repo root
python -m venv .venv
# Windows: .\.venv\Scripts\Activate.ps1 | *nix: source .venv/bin/activate

pip install -e .                    # installs compliance-collector (core)
pip install -e ./backend[dev]       # installs the backend + dev deps

cd backend
cp .env.example .env                # optional; dev mode works without env
uvicorn app.main:app --reload --port 8080
```

Open <http://localhost:8080/docs> for the Swagger UI.

> In `environment=dev` with `entra_app_client_id=""`, auth is bypassed
> and a fake Global Admin principal is injected. **Never deploy that way.**

---

## Tests

```bash
cd backend
pytest
```

Covers health, principal resolution, consent URL generation, assessment
CRUD, and 409/404 error paths. Graph + Entra are never hit during tests.

---

## Configuration

All settings are env-driven (see `app/config.py`):

| Variable | Purpose |
|---|---|
| `ENVIRONMENT` | `dev` / `staging` / `prod` |
| `CORS_ALLOW_ORIGINS` | JSON array of allowed UI origins |
| `ENTRA_APP_CLIENT_ID` | Our multi-tenant app registration |
| `ENTRA_APP_TENANT_ID` | `common` for multi-tenant, or a GUID |
| `ENTRA_API_AUDIENCE` | `api://<client_id>` |
| `GRAPH_AUTH_MODE` | `mi_fic` / `secret` / `cert` |
| `GRAPH_MANAGED_IDENTITY_CLIENT_ID` | User-assigned MI client ID |
| `GRAPH_CLIENT_SECRET` | Only when `GRAPH_AUTH_MODE=secret` |
| `GRAPH_CERT_PATH` | Only when `GRAPH_AUTH_MODE=cert` |
| `STORAGE_BACKEND` | `local` (v0.4) / `blob` (v0.5) |
| `STORAGE_LOCAL_PATH` | Path for local mode |

See `docs/backend-setup.md` in the repo root for the full Entra
multi-tenant + FIC walkthrough.
