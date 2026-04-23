"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useMsal } from "@azure/msal-react";

export default function AuthCallbackPage() {
  return <MsalCallback />;
}

function MsalCallback() {
  const router = useRouter();
  const { instance } = useMsal();
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    instance
      .initialize()
      .then(() => instance.handleRedirectPromise())
      .then((resp) => {
        if (resp?.account) {
          instance.setActiveAccount(resp.account);
        } else {
          const existing =
            instance.getActiveAccount() || instance.getAllAccounts()[0];
          if (existing) instance.setActiveAccount(existing);
        }
        router.replace("/");
      })
      .catch((err) => {
        console.error("[MSAL] redirect callback failed", err);
        // Show the error instead of silently looping back
        const msg = err?.errorDescription || err?.message || String(err);
        setError(msg);
      });
  }, [instance, router]);

  if (error) {
    return (
      <div className="min-h-screen bg-bg flex items-center justify-center p-6">
        <div className="card max-w-lg w-full space-y-4">
          <p className="font-semibold text-red-400">Sign-in failed</p>
          <p className="text-sm text-slate-300 font-mono break-all">{error}</p>
          <p className="text-xs text-slate-500">
            Common causes: wrong redirect URI registered in Entra, mismatched
            client ID, or the app registration does not have the user&apos;s
            tenant consented.
          </p>
          <a href="/" className="btn-primary inline-block text-center">
            Back to home
          </a>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-bg flex items-center justify-center">
      <p className="text-slate-400 text-sm">Completing sign-in…</p>
    </div>
  );
}
