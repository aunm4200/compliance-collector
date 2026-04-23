"use client";

import { EventType, PublicClientApplication } from "@azure/msal-browser";
import { MsalProvider } from "@azure/msal-react";
import { useEffect, useState } from "react";
import { getPortalConfig, initializeMsal } from "@/lib/msalConfig";

type AuthState =
  | { status: "loading" }
  | { status: "bypass" }
  | { status: "ready"; pca: PublicClientApplication }
  | { status: "misconfigured"; reason: string }
  | { status: "error"; message: string };

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [authState, setAuthState] = useState<AuthState>({ status: "loading" });

  useEffect(() => {
    getPortalConfig()
      .then((cfg) => {
        if (cfg.devBypassAuth) {
          setAuthState({ status: "bypass" });
          return;
        }
        if (!cfg.clientId) {
          setAuthState({
            status: "misconfigured",
            reason: "ENTRA_CLIENT_ID is not set. Add it to your Container App environment variables.",
          });
          return;
        }
        if (!cfg.apiScope) {
          setAuthState({
            status: "misconfigured",
            reason: "ENTRA_API_SCOPE is not set. Add it to your Container App environment variables.",
          });
          return;
        }

        initializeMsal()
          .then((instance) => {
            if (!instance) {
              setAuthState({ status: "misconfigured", reason: "MSAL failed to initialize." });
              return;
            }
            instance.addEventCallback((event) => {
              if (event.eventType === EventType.LOGIN_SUCCESS && event.payload) {
                const account = (event.payload as { account?: unknown }).account;
                if (account) instance.setActiveAccount(account as never);
              }
            });
            setAuthState({ status: "ready", pca: instance });
          })
          .catch((err) => {
            console.error("[AuthProvider] MSAL init failed", err);
            setAuthState({ status: "error", message: String(err) });
          });
      })
      .catch((err) => {
        console.error("[AuthProvider] Failed to fetch portal config", err);
        setAuthState({ status: "error", message: "Could not load portal configuration." });
      });
  }, []);

  if (authState.status === "loading") {
    return (
      <div className="min-h-screen bg-bg flex items-center justify-center">
        <span className="text-slate-400 text-sm">Initializing…</span>
      </div>
    );
  }

  if (authState.status === "misconfigured" || authState.status === "error") {
    const msg =
      authState.status === "misconfigured" ? authState.reason : authState.message;
    return (
      <div className="min-h-screen bg-bg flex items-center justify-center p-6">
        <div className="card max-w-lg w-full space-y-3 text-center">
          <p className="font-semibold text-red-400">Authentication not configured</p>
          <p className="text-sm text-slate-400">{msg}</p>
          <p className="text-xs text-slate-500">
            See the deployment guide for required environment variables.
          </p>
        </div>
      </div>
    );
  }

  if (authState.status === "bypass") {
    return <>{children}</>;
  }

  return <MsalProvider instance={authState.pca}>{children}</MsalProvider>;
}
