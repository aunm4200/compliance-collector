import Link from "next/link";

export default function Home() {
  return (
    <div className="space-y-8">
      <section className="card">
        <h1 className="text-3xl font-semibold">Evidence, on demand.</h1>
        <p className="mt-2 max-w-2xl text-slate-300">
          Start a fresh Microsoft 365 compliance assessment in one click. We
          pull live configuration from Microsoft Graph, evaluate it against
          the frameworks you pick, and hand you a tamper-evident evidence
          pack ready for your auditor.
        </p>
        <div className="mt-6 flex flex-wrap gap-3">
          <Link href="/assessments/new" className="btn-primary">
            Start assessment
          </Link>
          <Link href="/assessments" className="btn-ghost">
            View past assessments
          </Link>
        </div>
      </section>

      <section className="grid gap-4 md:grid-cols-3">
        <FeatureCard
          title="Cert-free auth"
          body="Managed Identity + federated credentials — no secrets to rotate, no certs to manage."
        />
        <FeatureCard
          title="Pick your frameworks"
          body="CIS M365 and SOC 2 today. ISO 27001, NIST CSF 2.0, and HIPAA on the roadmap."
        />
        <FeatureCard
          title="Tamper-evident evidence"
          body="Every run ships a SHA-256 manifest so auditors can verify nothing was edited."
        />
      </section>
    </div>
  );
}

function FeatureCard({ title, body }: { title: string; body: string }) {
  return (
    <div className="card">
      <h3 className="text-base font-semibold">{title}</h3>
      <p className="mt-1 text-sm text-slate-300">{body}</p>
    </div>
  );
}
