"use client";

import Link from "next/link";
import { useState } from "react";
import { useIsAuthenticated, useMsal } from "@azure/msal-react";
import { getPortalConfig } from "@/lib/msalConfig";

export function NavBar() {
  return (
    <header className="border-b border-border bg-panel/80 backdrop-blur">
      <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-4">
        <Link href="/" className="flex items-center gap-2">
          <div className="h-7 w-7 rounded bg-accent" />
          <span className="text-lg font-semibold">Compliance Collector</span>
        </Link>
        <nav className="flex items-center gap-4 text-sm">
          <Link href="/assessments" className="text-slate-300 hover:text-white">
            Assessments
          </Link>
          <Link href="/assessments/new" className="text-slate-300 hover:text-white">
            New assessment
          </Link>
          <Link href="/consent" className="text-slate-300 hover:text-white">
            Consent
          </Link>
          <MsalAuthButton />
        </nav>
      </div>
    </header>
  );
}

function MsalAuthButton() {
  const isAuthed = useIsAuthenticated();
  const { instance, accounts } = useMsal();
  const [signingIn, setSigningIn] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function signIn() {
    setSigningIn(true);
    setError(null);
    try {
      const cfg = await getPortalConfig();
      const loginRequest = {
        scopes: ["openid", "profile", "email", cfg.apiScope],
      };
      await instance.initialize();
      await instance.loginRedirect(loginRequest);
      // loginRedirect navigates away — no code runs after this
    } catch (err) {
      console.error("[MSAL] login failed", err);
      setError("Sign-in failed. Check the browser console for details.");
      setSigningIn(false);
    }
  }

  if (isAuthed) {
    return (
      <div className="flex items-center gap-3">
        <span className="text-xs text-slate-400">{accounts[0]?.name}</span>
        <button className="btn-ghost" onClick={() => instance.logoutRedirect()}>
          Sign out
        </button>
      </div>
    );
  }

  return (
    <div className="flex flex-col items-end gap-1">
      <button className="btn-primary" onClick={signIn} disabled={signingIn}>
        {signingIn ? "Redirecting…" : "Sign in"}
      </button>
      {error && <p className="text-xs text-red-400 max-w-xs text-right">{error}</p>}
    </div>
  );
}
