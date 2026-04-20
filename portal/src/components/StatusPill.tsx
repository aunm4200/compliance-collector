import type { RunStatus } from "@/lib/types";

export function StatusPill({ status }: { status: RunStatus | string }) {
  const cls =
    status === "succeeded"
      ? "pill-pass"
      : status === "failed" || status === "canceled"
      ? "pill-fail"
      : "pill-na";
  return <span className={cls}>{status}</span>;
}
