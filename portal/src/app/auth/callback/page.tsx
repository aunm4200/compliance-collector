"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useMsal } from "@azure/msal-react";
import { devBypassAuth } from "@/lib/msalConfig";

export default function AuthCallbackPage() {
  return devBypassAuth ? <DevBypassRedirect /> : <MsalCallback />;
}

function DevBypassRedirect() {
  const router = useRouter();
  useEffect(() => {
    router.replace("/");
  }, [router]);
  return <CallbackShell />;
}

function MsalCallback() {
  const router = useRouter();
  const { instance } = useMsal();
  useEffect(() => {
    instance
      .initialize()
      .then(() => instance.handleRedirectPromise())
      .then((resp) => {
        const account = resp?.account || instance.getActiveAccount() || instance.getAllAccounts()[0];
        if (account) instance.setActiveAccount(account);
      })
      .catch((err) => console.error("MSAL redirect error", err))
      .finally(() => router.replace("/"));
  }, [instance, router]);
  return <CallbackShell />;
}

function CallbackShell() {
  return (
    <div className="card">
      <p className="text-slate-300">Completing sign-in…</p>
    </div>
  );
}
