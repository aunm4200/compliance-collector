"use client";

import { PublicClientApplication, EventType } from "@azure/msal-browser";
import { MsalProvider } from "@azure/msal-react";
import { useMemo } from "react";
import { msalConfig, devBypassAuth } from "@/lib/msalConfig";

export function AuthProvider({ children }: { children: React.ReactNode }) {
  // Branch at the component boundary — each child calls hooks consistently.
  if (devBypassAuth) return <>{children}</>;
  return <MsalAuthProvider>{children}</MsalAuthProvider>;
}

function MsalAuthProvider({ children }: { children: React.ReactNode }) {
  const pca = useMemo(() => {
    if (typeof window === "undefined") return null;
    const instance = new PublicClientApplication(msalConfig);
    instance.addEventCallback((event) => {
      if (event.eventType === EventType.LOGIN_SUCCESS && event.payload) {
        const account = (event.payload as { account?: unknown }).account;
        if (account) instance.setActiveAccount(account as never);
      }
    });
    return instance;
  }, []);

  if (!pca) return <>{children}</>;
  return <MsalProvider instance={pca}>{children}</MsalProvider>;
}