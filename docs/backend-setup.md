# Backend setup — v0.4

This walks through everything you need to do **on your side** to bring
the v0.4 backend up end-to-end. Items marked **(one-time)** are only
needed once for the project; items marked **(per env)** are repeated per
environment (dev / staging / prod).

---

## 1. Register the multi-tenant Entra app (one-time)

In the **Azure portal → Microsoft Entra ID → App registrations → New registration**:

1. **Name**: `compliance-collector`
2. **Supported account types**: *Accounts in any organizational directory
   (Any Microsoft Entra ID tenant — Multitenant)*.
3. **Redirect URIs**: Add two entries under **Single-page application (SPA)**:
   * `http://localhost:3000/auth/callback` — MSAL sign-in redirect
   * `http://localhost:3000/consent/callback` — Admin consent return URI

   > For production, replace `http://localhost:3000` with your portal's FQDN
   > on both entries.
4. Click **Register**. Note the **Application (client) ID** — this is
   `ENTRA_APP_CLIENT_ID` throughout.

### Expose the API

Under **Expose an API**:

1. Set **Application ID URI** to `api://<client-id>` (default suggestion
   is fine).
2. Add a **scope** `access_as_user` — admin + user consent; "Admins and
   users can consent".

### Declare the Global Admin app role

Under **App roles → Create app role**:

| Field | Value |
|---|---|
| Display name | Global Administrator |
| Allowed member types | Users/Groups |
| Value | `GlobalAdministrator` |
| Description | Can initiate compliance assessments |

This is the role the backend checks via `require_global_admin`.

### API permissions (application, not delegated)

Add these **Microsoft Graph application** permissions — these are what
the admin consents to in their tenant:

* `Policy.Read.All`
* `Directory.Read.All`
* `AuditLog.Read.All`
* `Reports.Read.All`
* `RoleManagement.Read.Directory`

Do **not** grant admin consent in your own tenant for these — each
customer tenant will consent independently via the portal flow.

### Add delegated permissions for the portal UI

Under the same **API permissions**, add **delegated** `openid`,
`profile`, `email`, `offline_access`.

---

## 2. Provision Azure infrastructure (per env)

```bash
az group create -n rg-compliance-collector-dev -l eastus2

az deployment group create \
  -g rg-compliance-collector-dev \
  --template-file infra/main.bicep \
  --parameters infra/main.parameters.json \
  --parameters entraAppClientId=<client-id> entraApiAudience=api://<client-id>
```

Outputs include the backend FQDN, the user-assigned MI's **client ID**
and **principal ID**, and the ACR login server.

Costs at idle: ~$20–40 / month (Container Apps consumption + Log
Analytics + ACR Basic).

---

## 3. Wire up federated identity credentials (per env, one-time)

On the **Entra app registration → Certificates & secrets → Federated
credentials → Add credential**:

* **Scenario**: Other issuer
* **Issuer**: `https://login.microsoftonline.com/<your-tenant-id>/v2.0`
* **Subject identifier**: the user-assigned MI's **principal ID** from
  the Bicep output, formatted as
  `/eid1/c/pub/t/<tenant-id>/a/<mi-object-id>`
* **Audience**: `api://AzureADTokenExchange`

> The exact subject format depends on how Entra evolves the FIC spec;
> consult <https://learn.microsoft.com/entra/workload-id/workload-identity-federation-config-app-trust-managed-identity>
> for the current shape. The Azure CLI also has
> `az ad app federated-credential create` which fills it in for you.

Once this is in place, `GRAPH_AUTH_MODE=mi_fic` works with zero secrets.

---

## 4. Build and push the backend image (per release)

```bash
az acr login -n <acr-name>

docker build -t <acr-login-server>/compliance-collector-backend:0.4.0 .
docker push   <acr-login-server>/compliance-collector-backend:0.4.0

az containerapp update \
  -g rg-compliance-collector-dev \
  -n ccolXXXXXX-api \
  --image <acr-login-server>/compliance-collector-backend:0.4.0
```

---

## 5. Smoke test

```bash
curl https://<backend-fqdn>/healthz
# {"status":"ok","service":"compliance-collector-backend","version":"0.4.0","environment":"prod"}
```

For authenticated calls (`/auth/me`, `/assessments`), use the portal UI
once v0.5 lands, or a tool like `msal-cli` to mint a token against the
`access_as_user` scope.

---

## What's shipping in v0.5

* Next.js + MSAL.js portal UI with framework selector
* Admin-consent callback handling end-to-end
* Cosmos DB persistence (replaces in-memory consent/state)
* Azure Blob Storage backend for evidence
* Key Vault for rotating secrets (for `secret` mode only — `mi_fic` stays secret-free)
