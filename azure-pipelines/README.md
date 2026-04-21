# Azure Pipelines

Two pipelines live here. Both are YAML-authored, no Classic UI.

| File | Trigger | Purpose |
|---|---|---|
| `ci.yml` | Push + PR to `main` | Lints + tests core, backend, portal. Optional — only needed if you're migrating off the GitHub Actions workflows under `.github/workflows/`. |
| `deploy.yml` | Manual (`workflow_dispatch` equivalent) | Builds + pushes both images to ACR, then rolls out the two Container Apps. |

## One-time setup in Azure DevOps

1. **Project** → create `compliance-collector` (Team Services or on-prem
   doesn't matter).
2. **Service connections** → new → *Azure Resource Manager* → **Workload
   Identity Federation (automatic)** → scope it to your resource group
   (`rg-compliance-collector`). Name it `sc-ccol`.
3. **Service connections** → new → *Docker Registry* → Azure Container
   Registry → pick the ACR created by Bicep. *OR* reuse the ARM
   connection above for `Docker@2` with `containerRegistry:
   $(AZURE_SUBSCRIPTION_CONNECTION)` — that's what `deploy.yml` does.
4. **Pipelines → Library → Variable groups** → new group
   `compliance-collector-azure` with the variables listed at the top of
   `deploy.yml`. Mark secret variables as locked.
5. **Pipelines → Environments** → new environment
   `compliance-collector-prod` (add approvers if you want a gate before
   Deploy stage runs).
6. **Pipelines → New pipeline** → point at this repo, use existing YAML:
   - `/azure-pipelines/deploy.yml` — save, don't run yet.
   - `/azure-pipelines/ci.yml` — save. It'll run on the next push.

## First deploy

Once Bicep infra exists and the variable group is populated:

Pipelines → Compliance Collector Deploy → **Run pipeline** → enter tag
(default `0.6.0`) → Run. Watch Build stage, approve Deploy stage if
environment approvers are configured, done.

See `docs/v0.6-deploy.md` for the full end-to-end walkthrough including
Entra app registration, UAMI FIC, and the initial Bicep deploy.
