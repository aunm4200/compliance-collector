"use client";

import { useState } from "react";
import useSWR from "swr";
import { api } from "@/lib/api";
import { devBypassAuth } from "@/lib/msalConfig";
import type { ConsentRecord, ConsentInitResponse } from "@/lib/types";

export default function ConsentPage() {
  if (devBypassAuth) {
    return (
      <div className="card max-w-xl">
        <h1 className="text-2xl font-semibold">Admin consent</h1>
        <p className="mt-2 text-slate-300">
          Dev bypass is enabled — consent is not required in dev mode.
        </p>
      </div>
    );
  }
  return <ConsentView />;
}

function ConsentView() {
  const [granting, setGranting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const { data: record, isLoading } = useSWR<ConsentRecord>(
    "/consent/status",
    (path: string) => api<ConsentRecord>(path),
  );

  async function grantConsent() {
    setGranting(true);
    setError(null);
    try {
      const callbackUri = `${window.location.origin}/consent/callback`;
      const resp = await api<ConsentInitResponse>(
        `/consent/url?redirect_uri=${encodeURIComponent(callbackUri)}`,
      );
      // Hard-navigate so Microsoft can redirect back to /consent/callback
      window.location.href = resp.consent_url;
    } catch (e: any) {
      setError(e?.message || "Failed to generate consent URL.");
      setGranting(false);
    }
  }

  const granted = record?.status === "granted";

  return (
    <div className="space-y-6 max-w-xl">
      <div>
        <h1 className="text-2xl font-semibold">Admin consent</h1>
        <p className="mt-1 text-sm text-slate-400">
          Compliance Collector needs read-only access to your Microsoft 365
          tenant to collect evidence. This is a one-time admin consent.
        </p>
      </div>

      <div className="card space-y-4">
        <div className="flex items-center justify-between">
          <span className="font-medium">Consent status</span>
          {isLoading ? (
            <span className="text-slate-400 text-sm">Checking…</span>
          ) : granted ? (
            <span className="pill-pass">Granted</span>
          ) : (
            <span className="pill-fail">Not granted</span>
          )}
        </div>

        {granted && record?.granted_by_name && (
          <p className="text-sm text-slate-400">
            Granted by <span className="text-slate-200">{record.granted_by_name}</span>
            {record.consent_granted_at && (
              <> on {new Date(record.consent_granted_at).toLocaleString()}</>
            )}
          </p>
        )}

        {granted && (
          <div>
            <p className="text-xs font-medium text-slate-400 mb-1">Consented scopes</p>
            <ul className="space-y-0.5">
              {(record?.scopes ?? []).map((s) => (
                <li key={s} className="text-xs font-mono text-slate-300">
                  {s}
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>

      {!granted && (
        <div className="card border-accent/30 space-y-3">
          <h2 className="font-semibold">Grant access</h2>
          <p className="text-sm text-slate-300">
            You will be redirected to Microsoft's admin consent page. Sign in as
            a Global Administrator and approve the permissions below.
          </p>
          <ul className="text-sm text-slate-400 space-y-1 list-disc list-inside">
            <li>Policy.Read.All</li>
            <li>Directory.Read.All</li>
            <li>AuditLog.Read.All</li>
            <li>Reports.Read.All</li>
            <li>RoleManagement.Read.Directory</li>
          </ul>
          {error && <p className="text-red-400 text-sm">{error}</p>}
          <button
            className="btn-primary"
            onClick={grantConsent}
            disabled={granting}
          >
            {granting ? "Redirecting…" : "Grant admin consent"}
          </button>
        </div>
      )}
    </div>
  );
}
