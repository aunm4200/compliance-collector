"use client";

import { Configuration, LogLevel, PublicClientApplication } from "@azure/msal-browser";

// Build-time flag for UI hints (consent banner, etc.).
// Defaults to false so production images never bypass auth.
// The authoritative runtime value lives in getPortalConfig().devBypassAuth.
export const devBypassAuth = process.env.NEXT_PUBLIC_DEV_BYPASS_AUTH === "true";

export interface PortalConfig {
  clientId: string;
  authority: string;
  redirectUri: string;
  apiScope: string;
  devBypassAuth: boolean;
}

// ── Runtime config ─────────────────────────────────────────────────────────
// Fetched from /api/config (server-side env vars) once per page load.
// This avoids baking Entra values into the Next.js bundle at docker-build time.

let _configCache: PortalConfig | null = null;
let _configPromise: Promise<PortalConfig> | null = null;

export async function getPortalConfig(): Promise<PortalConfig> {
  if (_configCache) return _configCache;
  if (!_configPromise) {
    _configPromise = fetch("/api/config")
      .then((r) => {
        if (!r.ok) throw new Error(`/api/config returned ${r.status}`);
        return r.json() as Promise<PortalConfig>;
      })
      .then((cfg) => {
        _configCache = cfg;
        return cfg;
      })
      .catch((err) => {
        _configPromise = null; // allow retry on next call
        throw err;
      });
  }
  return _configPromise;
}

// ── MSAL singleton ─────────────────────────────────────────────────────────

let _msalInstance: PublicClientApplication | null = null;
let _msalInitPromise: Promise<PublicClientApplication | null> | null = null;

export async function initializeMsal(): Promise<PublicClientApplication | null> {
  if (typeof window === "undefined") return null;

  if (!_msalInitPromise) {
    _msalInitPromise = (async () => {
      const cfg = await getPortalConfig();

      if (cfg.devBypassAuth || !cfg.clientId) return null;

      const msalConfig: Configuration = {
        auth: {
          clientId: cfg.clientId,
          authority: cfg.authority || "https://login.microsoftonline.com/common",
          redirectUri: cfg.redirectUri || `${window.location.origin}/auth/callback`,
          postLogoutRedirectUri: window.location.origin,
          navigateToLoginRequestUrl: true,
        },
        cache: {
          cacheLocation: "sessionStorage",
          storeAuthStateInCookie: false,
        },
        system: {
          loggerOptions: {
            loggerCallback: (level, message, containsPii) => {
              if (containsPii) return;
              if (level === LogLevel.Error) console.error("[MSAL]", message);
              if (level === LogLevel.Warning) console.warn("[MSAL]", message);
            },
            logLevel: LogLevel.Warning,
          },
        },
      };

      if (!_msalInstance) {
        _msalInstance = new PublicClientApplication(msalConfig);
      }

      await _msalInstance.initialize();

      const existingAccount =
        _msalInstance.getActiveAccount() || _msalInstance.getAllAccounts()[0];
      if (existingAccount) _msalInstance.setActiveAccount(existingAccount);

      return _msalInstance;
    })().catch((err) => {
      _msalInitPromise = null; // allow retry
      throw err;
    });
  }

  return _msalInitPromise;
}
