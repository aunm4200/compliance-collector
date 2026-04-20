"use client";

import useSWR from "swr";
import Link from "next/link";
import { api } from "@/lib/api";
import type { Assessment, ReportSummary } from "@/lib/types";
import { StatusPill } from "@/components/StatusPill";

export default function AssessmentDetailPage({
  params,
}: {
  params: { id: string };
}) {
  const { id } = params;

  const { data: assessment, error } = useSWR<Assessment>(
    `/assessments/${id}`,
    (path: string) => api<Assessment>(path),
    {
      refreshInterval: (latest) =>
        latest && (latest.status === "succeeded" || latest.status === "failed") ? 0 : 3000,
    },
  );

  const succeeded = assessment?.status === "succeeded";

  const { data: summary } = useSWR<ReportSummary>(
    succeeded ? `/assessments/${id}/report/summary` : null,
    (path: string) => api<ReportSummary>(path),
  );

  if (error) return <p className="text-red-400">Failed to load: {String(error)}</p>;
  if (!assessment) return <p className="text-slate-400">Loading…</p>;

  return (
    <div className="space-y-6">
      <div>
        <Link href="/assessments" className="text-sm text-slate-400 hover:text-white">
          ← Back to assessments
        </Link>
        <h1 className="mt-2 text-2xl font-semibold">
          {assessment.label || `Assessment ${assessment.id.slice(0, 8)}`}
        </h1>
        <div className="mt-1 flex flex-wrap items-center gap-3 text-sm text-slate-400">
          <StatusPill status={assessment.status} />
          <span>Frameworks: {assessment.frameworks.join(", ")}</span>
          <span>Evidence files: {assessment.evidence_file_count}</span>
        </div>
      </div>

      {assessment.status === "queued" && (
        <div className="card text-slate-300">
          <p>Queued. Waiting for a worker to pick this up…</p>
        </div>
      )}

      {assessment.status === "running" && (
        <div className="card text-slate-300">
          <p>Collecting evidence from Microsoft Graph. This usually takes 30–90 seconds.</p>
          <div className="mt-3 h-1.5 w-full overflow-hidden rounded-full bg-panelLight">
            <div className="h-full w-1/3 animate-pulse bg-accent" />
          </div>
        </div>
      )}

      {assessment.status === "failed" && (
        <div className="card border-red-500/30">
          <h3 className="font-semibold text-red-300">Assessment failed</h3>
          <p className="mt-1 text-sm text-slate-300">
            {assessment.error_message || "No error message provided."}
          </p>
        </div>
      )}

      {succeeded && summary && <ResultsView summary={summary} assessment={assessment} />}
    </div>
  );
}

function ResultsView({
  summary,
  assessment,
}: {
  summary: ReportSummary;
  assessment: Assessment;
}) {
  const { pass = 0, fail = 0, na = 0, error = 0 } = summary.totals;
  const total = pass + fail + na + error;
  return (
    <div className="space-y-6">
      <div className="grid gap-4 md:grid-cols-4">
        <KpiCard label="Total controls" value={total} tone="na" />
        <KpiCard label="Pass" value={pass} tone="pass" />
        <KpiCard label="Fail" value={fail} tone="fail" />
        <KpiCard label="Not applicable" value={na + error} tone="na" />
      </div>

      <div className="flex flex-wrap gap-3">
        <a
          href={`/api/backend/assessments/${assessment.id}/report/html`}
          target="_blank"
          rel="noreferrer"
          className="btn-primary"
        >
          Open HTML report
        </a>
      </div>

      <div className="card">
        <h3 className="text-lg font-semibold">Findings</h3>
        <div className="mt-4 overflow-hidden rounded-lg border border-border">
          <table className="w-full text-sm">
            <thead className="bg-panelLight text-left text-slate-300">
              <tr>
                <th className="px-3 py-2 font-medium">Control</th>
                <th className="px-3 py-2 font-medium">Framework</th>
                <th className="px-3 py-2 font-medium">Status</th>
                <th className="px-3 py-2 font-medium">Reason</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border bg-panel">
              {summary.findings.map((f) => (
                <tr key={`${f.framework}-${f.control_id}`}>
                  <td className="px-3 py-2">
                    <div className="font-medium">{f.control_id}</div>
                    <div className="text-xs text-slate-400">{f.title}</div>
                  </td>
                  <td className="px-3 py-2 text-slate-300">{f.framework}</td>
                  <td className="px-3 py-2">
                    <StatusPill status={f.status === "not_applicable" ? "na" : f.status} />
                  </td>
                  <td className="px-3 py-2 text-slate-300">
                    {f.reasons[0] || <span className="text-slate-500">—</span>}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

function KpiCard({
  label,
  value,
  tone,
}: {
  label: string;
  value: number;
  tone: "pass" | "fail" | "na";
}) {
  const color =
    tone === "pass" ? "text-pass" : tone === "fail" ? "text-fail" : "text-slate-200";
  return (
    <div className="card">
      <div className="text-sm text-slate-400">{label}</div>
      <div className={`mt-1 text-3xl font-semibold ${color}`}>{value}</div>
    </div>
  );
}
