"use client";

import { useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { api } from "@/lib/api";
import type { ConsentRecord } from "@/lib/types";

export default function ConsentCallbackPage() {
  const router = useRouter();
  const params = useSearchParams();
  const [status, setStatus] = useState<"processing" | "success" | "denied" | "error">(
    "processing",
  );
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const tenant = params.get("tenant");
    const state = params.get("state");
    const adminConsent = params.get("admin_consent");

    if (!tenant || !state) {
      setError("Missing required parameters from Microsoft redirect.");
      setStatus("error");
      return;
    }

    if (adminConsent === "False") {
      setStatus("denied");
      return;
    }

    const qs = new URLSearchParams({
      tenant,
      state,
      admin_consent: adminConsent === "True" ? "true" : "false",
    });

    api<ConsentRecord>(`/consent/callback?${qs.toString()}`, { method: "POST" })
      .then(() => {
        setStatus("success");
        setTimeout(() => router.replace("/consent"), 2000);
      })
      .catch((e: any) => {
        setError(e?.message || "Failed to record consent.");
        setStatus("error");
      });
  }, [params, router]);

  return (
    <div className="card max-w-md mx-auto mt-16 space-y-3">
      {status === "processing" && (
        <>
          <h2 className="font-semibold text-lg">Recording consent…</h2>
          <p className="text-slate-400 text-sm">Just a moment.</p>
        </>
      )}
      {status === "success" && (
        <>
          <h2 className="font-semibold text-lg text-pass">Consent granted!</h2>
          <p className="text-slate-300 text-sm">
            Redirecting you back to the consent page…
          </p>
        </>
      )}
      {status === "denied" && (
        <>
          <h2 className="font-semibold text-lg text-fail">Consent declined</h2>
          <p className="text-slate-300 text-sm">
            You declined the admin consent. Assessments require Graph API access.
          </p>
          <button className="btn-ghost" onClick={() => router.replace("/consent")}>
            Back to consent
          </button>
        </>
      )}
      {status === "error" && (
        <>
          <h2 className="font-semibold text-lg text-fail">Something went wrong</h2>
          <p className="text-red-400 text-sm">{error}</p>
          <button className="btn-ghost" onClick={() => router.replace("/consent")}>
            Back to consent
          </button>
        </>
      )}
    </div>
  );
}
