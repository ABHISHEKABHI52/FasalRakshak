import Link from "next/link";

import { Badge, Button, Card } from "@/components/ui";
import { env } from "@/lib/env";

const CAPABILITIES = [
  {
    title: "Image quality gate",
    body: "Unusable photos are rejected before any analysis, with specific retake guidance — no guessing from a blurred leaf.",
  },
  {
    title: "Adaptive questions",
    body: "When visual evidence is insufficient, FasalRakshak asks only the questions that reduce uncertainty, then re-evaluates.",
  },
  {
    title: "3 / 7 / 14-day risk",
    body: "Diagnosis confidence, current risk and escalation risk are reported separately, with the factors that drove them.",
  },
] as const;

export default function HomePage() {
  return (
    <main className="mx-auto flex max-w-5xl flex-col gap-10 px-5 py-10">
      <header className="flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <span aria-hidden className="grid h-11 w-11 place-items-center rounded-xl bg-field-600 text-xl">
            🌿
          </span>
          <div>
            <h1 className="text-xl font-semibold leading-tight">{env.appName}</h1>
            <p className="text-sm text-slate-600">{env.tagline}</p>
          </div>
        </div>
        <nav className="flex items-center gap-3">
          <Link href="/login" className="text-sm font-medium text-field-700 underline-offset-4 hover:underline">
            Sign in
          </Link>
        </nav>
      </header>

      <section className="flex flex-col gap-4">
        <Badge tone="info">Smart India Hackathon 2026 · SIH26131 · Software</Badge>
        <h2 className="text-3xl font-semibold tracking-tight sm:text-4xl">
          AI-Powered Crop Health &amp; Early Warning Platform
        </h2>
        <p className="max-w-2xl text-slate-700">
          FasalRakshak is a decision-support platform for crop disease and pest management — not a photo
          classifier. When evidence is insufficient it says so and asks targeted questions instead of forcing a
          diagnosis.
        </p>
        <p className="text-lg font-medium text-field-700">Evidence &gt; Guess</p>
      </section>

      <section className="grid gap-4 sm:grid-cols-3">
        {CAPABILITIES.map((item) => (
          <Card key={item.title}>
            <h3 className="font-semibold">{item.title}</h3>
            <p className="mt-2 text-sm text-slate-700">{item.body}</p>
          </Card>
        ))}
      </section>

      <Card className="bg-field-50">
        <h3 className="font-semibold">Implementation status</h3>
        <p className="mt-2 text-sm text-slate-700">
          Phase 1 (platform foundation) is implemented: repository structure, FastAPI service, PostgreSQL +
          PostGIS + pgvector configuration, Alembic migrations, authentication, RBAC, and health/readiness
          checks. Crop scanning, the AI pipeline, the risk engine, GIS intelligence, RAG, weather and the
          expert/officer workflows are <strong>not implemented yet</strong> — they arrive in later phases as
          planned in the architecture documentation.
        </p>
        <div className="mt-4 flex flex-wrap gap-3">
          <Link href="/login">
            <Button>Sign in</Button>
          </Link>
          <a href={`${env.apiUrl}/api/docs`} target="_blank" rel="noreferrer">
            <Button variant="secondary">API documentation</Button>
          </a>
        </div>
      </Card>

      <footer className="border-t border-slate-200 pt-5 text-sm text-slate-600">
        <p>
          FasalRakshak is a decision-support tool. It does not replace expert, KVK or agriculture-officer
          advice.
        </p>
        <p className="mt-1">FasalRakshak — Scan. Predict. Protect.</p>
      </footer>
    </main>
  );
}