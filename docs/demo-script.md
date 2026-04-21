# Demo script — compliance-collector v0.6

A 10-minute walkthrough for a manager or prospective client. Assumes the
Azure deployment in `v0.6-deploy.md` is live and you have both URLs.

## Pre-flight (5 min before)

1. Warm the apps — hit `https://<backend>/health` and the portal homepage
   so the first demo click isn't a cold start.
2. Open two tabs: portal landing page + `docs/v0.3-admin-consent.md` (as a
   fallback for deep questions).
3. Have a demo tenant signed in on a separate browser profile — Global
   Admin account, **not** your production admin.

## Act 1 — The problem (1 min)

> "Tenant admins are expected to prove CIS Microsoft 365 and SOC 2
> controls are met. Today, that's a spreadsheet and a week of screenshots.
> We automate the evidence collection and the pass/fail evaluation."

## Act 2 — Sign-in & consent (2 min)

1. Click **Sign in** on the portal. MSAL popup opens.
2. Sign in as demo-tenant Global Admin. Admin consent prompt appears the
   first time.
3. Point out: *"This is the Microsoft-managed consent flow. No cert
   exchange, no secrets. Same mechanism any Microsoft partner app uses."*

## Act 3 — Start an assessment (2 min)

1. Navigate to **Assessments → New**.
2. Tick **CIS Microsoft 365 v3.0** and **SOC 2 CC6 (Logical Access)**.
3. Click **Start assessment**.
4. Show the status flip from `queued` → `running`. Portal polls every 3s.

> "Under the hood, the backend is authenticating to Graph as a federated
> identity — a User-Assigned Managed Identity in our subscription acts as
> the credential. No secret ever leaves Azure."

## Act 4 — Read the report (3 min)

When the run flips to `completed`:

1. Click into the assessment. KPI cards show pass/fail/NA counts.
2. Scroll the findings table — point out one PASS and one FAIL with
   expandable evidence.
3. Click **Open full HTML report** — renders the v0.3 static report in a
   new tab.

## Act 5 — Wrap (2 min)

* **Cost story**: ~$15–40/month per tenant on demo scale. Scales to zero
  between runs.
* **Security story**: UAMI + FIC, no secrets. Multi-tenant consent means
  the customer's admin controls the grant and can revoke it in one click.
* **Extensibility story**: adding a new control = YAML + a collector.
  Show the v0.3 `controls/cis_m365_v3.yaml` snippet if asked.

## If something goes wrong

| Symptom | Recover |
|---|---|
| Portal cold start (>10 s blank) | "Demo env scales to zero; prod would keep warm replicas." |
| Graph 403 on consent | "Demo tenant hasn't consented to app-permissions yet — normally part of onboarding." |
| Assessment stuck `running` | Refresh — backend logs to Log Analytics, you can `az containerapp logs show` live. |
| Portal auth popup blocked | Browser popup blocker; use the redirect flow (already the default on Safari). |

## Followups to collect

* Which frameworks beyond CIS + SOC 2 matter to the prospect?
* How many tenants would they onboard month 1?
* Do they want evidence exported to their SIEM / GRC tool?
