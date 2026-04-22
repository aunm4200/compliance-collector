"use client";

import Link from "next/link";
import { useIsAuthenticated, useMsal } from "@azure/msal-react";
import { devBypassAuth, loginRequest } from "@/lib/msalConfig";

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
          {!devBypassAuth && (
            <Link href="/consent" className="text-slate-300 hover:text-white">
              Consent
            </Link>
          )}
          {devBypassAuth ? <DevModePill /> : <MsalAuthButton />}
        </nav>
      </div>
    </header>
  );
}

function DevModePill() {
  return <span className="pill-na">dev mode</span>;
}

function MsalAuthButton() {
  const isAuthed = useIsAuthenticated();
  const { instance, accounts } = useMsal();

  async function signIn() {
    try {
      await instance.initialize();
      await instance.loginRedirect(loginRequest);
    } catch (err) {
      console.error("MSAL login failed", err);
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
    <button className="btn-primary" onClick={signIn}>
      Sign in
    </button>
  );
}
