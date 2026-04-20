"use client";

import useSWR from "swr";
import Link from "next/link";
import { api } from "@/lib/api";
import type { AssessmentList } from "@/lib/types";
import { StatusPill } from "@/components/StatusPill";

export default function AssessmentsPage() {
  const { data, error, isLoading } = useSWR<AssessmentList>(
    "/assessments",
    (path: string) => api<AssessmentList>(path),
    { refreshInterval: 5000 },
  );

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold">Assessments</h1>
        <Link href="/assessments/new" className="btn-primary">
          New assessment
        </Link>
      </div>

      {isLoading && <p className="text-slate-400">Loading…</p>}
      {error && <p className="text-red-400">Failed to load: {String(error)}</p>}

      {data && data.items.length === 0 && (
        <div className="card text-slate-300">
          No assessments yet. <Link href="/assessments/new" className="text-accent underline">Start one</Link>.
        </div>
      )}

      {data && data.items.length > 0 && (
        <div className="overflow-hidden rounded-xl border border-border">
          <table className="w-full text-sm">
            <thead className="bg-panelLight text-left text-slate-300">
              <tr>
                <th className="px-4 py-3 font-medium">Label</th>
                <th className="px-4 py-3 font-medium">Frameworks</th>
                <th className="px-4 py-3 font-medium">Status</th>
                <th className="px-4 py-3 font-medium">Started</th>
                <th className="px-4 py-3" />
              </tr>
            </thead>
            <tbody className="divide-y divide-border bg-panel">
              {data.items.map((a) => (
                <tr key={a.id}>
                  <td className="px-4 py-3 text-slate-100">
                    {a.label || <span className="text-slate-500">(no label)</span>}
                  </td>
                  <td className="px-4 py-3 text-slate-300">{a.frameworks.join(", ")}</td>
                  <td className="px-4 py-3"><StatusPill status={a.status} /></td>
                  <td className="px-4 py-3 text-slate-400">
                    {a.started_at ? new Date(a.started_at).toLocaleString() : "—"}
                  </td>
                  <td className="px-4 py-3 text-right">
                    <Link className="text-accent hover:underline" href={`/assessments/${a.id}`}>
                      View
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
