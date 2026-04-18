# Setup Guide

This guide walks you through everything needed to run your first evidence collection.

## 1. Register an Entra app

1. Go to [Entra Admin Center](https://entra.microsoft.com) → **Applications** → **App registrations** → **New registration**.
2. Name: `compliance-collector`
3. Supported account types: **Single tenant**.
4. Redirect URI: leave blank.
5. Click **Register**.
6. On the overview page, copy the **Application (client) ID** and **Directory (tenant) ID** — you'll need these.

## 2. Grant API permissions (read-only)

Under **API permissions** → **Add a permission** → **Microsoft Graph** → **Application permissions**, add:

| Permission | Why |
|---|---|
| `Policy.Read.All` | Conditional Access, authentication methods |
| `Directory.Read.All` | Users, groups, roles |
| `AuditLog.Read.All` | Sign-ins, admin activity |
| `RoleManagement.Read.All` | Privileged role assignments |
| `Reports.Read.All` | MFA and license usage reports |
| `DeviceManagementConfiguration.Read.All` | Intune policies |
| `InformationProtectionPolicy.Read.All` | DLP / sensitivity labels |

Click **Grant admin consent for \<tenant\>**. All permissions must show a green checkmark.

## 3. Create and upload a certificate

### On macOS/Linux

```bash
openssl req -x509 -newkey rsa:4096 -nodes \
  -keyout auth.key \
  -out auth.crt \
  -days 365 \
  -subj "/CN=compliance-collector"

# Combine into a single PEM (for azure-identity)
cat auth.key auth.crt > auth.pem

# Keep auth.pem secure — add to .gitignore. Never commit.
```

### On Windows (PowerShell)

```powershell
$cert = New-SelfSignedCertificate `
  -Subject "CN=compliance-collector" `
  -CertStoreLocation "Cert:\CurrentUser\My" `
  -KeyExportPolicy Exportable `
  -KeySpec Signature `
  -KeyLength 4096 `
  -HashAlgorithm SHA256 `
  -NotAfter (Get-Date).AddYears(1)

# Export public cert (upload to Entra)
Export-Certificate -Cert $cert -FilePath .\auth.crt

# Export private key + cert as PFX, then convert to PEM with openssl or Git Bash
$pwd = ConvertTo-SecureString -String "temp" -Force -AsPlainText
Export-PfxCertificate -Cert $cert -FilePath .\auth.pfx -Password $pwd
```

Upload `auth.crt` to your app registration:
**Certificates & secrets** → **Certificates** → **Upload certificate**.

## 4. Install compliance-collector

```bash
# With pipx (recommended for isolated CLI tools)
pipx install compliance-collector

# Or with pip in a venv
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install compliance-collector
```

## 5. Run your first collection

```bash
compliance-collector collect \
  --tenant-id 00000000-0000-0000-0000-000000000000 \
  --client-id 11111111-1111-1111-1111-111111111111 \
  --cert-path ./auth.pem \
  --output ./evidence
```

You should see output like:

```
compliance-collector v0.1.0
Tenant: 00000000-...
Output: ./evidence/20260417T120000Z

Collection Results
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━┳━━━━━━━┓
┃ Collector                    ┃ Status ┃ Items ┃
┡━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━╇━━━━━━━┩
│ conditional_access_policies  │ OK     │ 12    │
└──────────────────────────────┴────────┴───────┘

✓ Manifest written: evidence/20260417T120000Z/manifest.json
✓ 1 evidence files collected.
```

## 6. Inspect the evidence

```bash
ls evidence/20260417T120000Z/
# conditional_access_policies.json
# manifest.json

cat evidence/20260417T120000Z/manifest.json | head -30
```

## Troubleshooting

| Error | Fix |
|---|---|
| `AADSTS700027: Client assertion contains an invalid signature` | Certificate on disk doesn't match the one uploaded to Entra. Re-upload `auth.crt`. |
| `Authorization_RequestDenied` | Missing Graph permission or admin consent not granted. Check step 2. |
| `Insufficient privileges to complete the operation` | App registration permissions are *delegated* not *application*. Re-add as **Application permissions**. |
