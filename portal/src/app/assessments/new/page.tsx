"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";
import { FRAMEWORKS, type Assessment, type Framework } from "@/lib/types";

const ENABLED: Framework[] = ["cis-m365", "soc2"];

export default function NewAssessmentPage() {
  const router = useRouter();
  const [selected, setSelected] = useState<Framework[]>(["cis-m365"]);
  const [label, setLabel] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  function toggle(id: Framework) {
    if (!ENABLED.includes(id)) return;
    setSelected((prev) => (prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]));
  }

  async function submit() {
    if (selected.length === 0) {
      setError("Pick at least one framework.");
      return;
    }
    setSubmitting(true);
    setError(null);
    try {
      const body = { frameworks: selected, label: label.trim() || null };
      const created = await api<Assessment>("/assessments", {
        method: "POST",
        body: JSON.stringify(body),
      });
      router.push(`/assessments/${created.id}`);
    } catch (e: any) {
      setError(e?.message || "Failed to start assessment.");
      setSubmitting(false);
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold">New assessment</h1>
        <p className="mt-1 text-sm text-slate-400">
          Choose which frameworks to evaluate against. The backend pulls live
          evidence from your Microsoft 365 tenant and scores each control.
        </p>
      </div>

      <div className="card space-y-4">
        <label className="block">
          <span className="text-sm font-medium text-slate-200">Label (optional)</span>
          <input
            type="text"
            value={label}
            onChange={(e) => setLabel(e.target.value)}
            maxLength={200}
            placeholder="Q2 SOC 2 evidence refresh"
            className="mt-1 w-full rounded-md border border-border bg-panelLight px-3 py-2 text-slate-100 placeholder:text-slate-500 focus:border-accent focus:outline-none"
          />
        </label>
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        {FRAMEWORKS.map((f) => {
          const enabled = ENABLED.includes(f.id);
          const checked = selected.includes(f.id);
          return (
            <button
              key={f.id}
              type="button"
              disabled={!enabled}
              onClick={() => toggle(f.id)}
              className={`card text-left transition ${
                checked ? "ring-2 ring-accent" : ""
              } ${enabled ? "hover:bg-panelLight" : "cursor-not-allowed opacity-50"}`}
            >
              <div className="flex items-start justify-between gap-2">
                <h3 className="text-base font-semibold">{f.label}</h3>
                {checked && <span className="pill-pass">selected</span>}
                {!enabled && <span className="pill-na">soon</span>}
              </div>
              <p className="mt-1 text-sm text-slate-300">{f.description}</p>
            </button>
          );
        })}
      </div>

      {error && <p className="text-sm text-red-400">{error}</p>}

      <div className="flex justify-end">
        <button className="btn-primary" disabled={submitting} onClick={submit}>
          {submitting ? "Starting…" : "Start assessment"}
        </button>
      </div>
    </div>
  );
}
