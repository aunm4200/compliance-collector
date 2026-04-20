export type RunStatus = "queued" | "running" | "succeeded" | "failed" | "canceled";

export type Framework = "cis-m365" | "soc2" | "iso27001" | "nist-csf" | "hipaa";

export interface Assessment {
  id: string;
  tenant_id: string;
  initiated_by_oid: string;
  initiated_by_name: string;
  label: string | null;
  frameworks: Framework[];
  status: RunStatus;
  created_at: string;
  updated_at: string;
  started_at: string | null;
  completed_at: string | null;
  evidence_file_count: number;
  error_message: string | null;
}

export interface AssessmentList {
  items: Assessment[];
  total: number;
}

export interface ControlFinding {
  control_id: string;
  framework: string;
  title: string;
  status: "pass" | "fail" | "not_applicable" | "error";
  reasons: string[];
}

export interface ReportSummary {
  assessment_id: string;
  tenant_id: string;
  generated_at: string;
  totals: Record<string, number>;
  per_framework: Record<string, Record<string, number>>;
  findings: ControlFinding[];
  html_report_url: string | null;
  manifest_url: string | null;
}

export interface Principal {
  subject: string;
  tenant_id: string;
  object_id: string;
  name: string;
  email: string;
  roles: string[];
}

export const FRAMEWORKS: { id: Framework; label: string; description: string }[] = [
  {
    id: "cis-m365",
    label: "CIS M365 Foundations",
    description: "Center for Internet Security benchmark for Microsoft 365.",
  },
  {
    id: "soc2",
    label: "SOC 2 Type II",
    description: "Trust Services Criteria relevant to M365 controls.",
  },
  {
    id: "iso27001",
    label: "ISO 27001 (coming soon)",
    description: "Information security management system controls.",
  },
  {
    id: "nist-csf",
    label: "NIST CSF 2.0 (coming soon)",
    description: "Cybersecurity Framework core functions.",
  },
  {
    id: "hipaa",
    label: "HIPAA Security Rule (coming soon)",
    description: "Administrative, physical, and technical safeguards.",
  },
];
