"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { api } from "@/lib/api-client";
import { useAuth } from "@/lib/auth_context";
import { Button, Card } from "@/components/ui";
import type { CropCycleDto, ScanDto } from "@/types/api";

export default function ScansPage() {
  const params = useParams();
  const router = useRouter();
  const { token, signOut } = useAuth();
  const farmId = params.farmId as string;
  const fieldId = params.fieldId as string;
  const cycleId = params.cycleId as string;
  const [cycle, setCycle] = useState<CropCycleDto | null>(null);
  const [scans, setScans] = useState<ScanDto[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!token) { router.replace("/login"); return; }
    let cancelled = false;
    Promise.all([
      api.cropCycles.get(token, cycleId),
      api.scans.listByField(token, fieldId),
    ])
      .then(([c, ss]) => { if (!cancelled) { setCycle(c); setScans(ss.items); setLoading(false) ; } })
      .catch(() => { if (!cancelled) router.replace(`/dashboard/farms/${farmId}/fields/${fieldId}`); });
    return () => { cancelled = true; };
  }, [token, cycleId, fieldId, farmId, router]);

  const cycleScans = scans.filter((s) => s.crop_cycle_id === cycleId);

  if (loading) {
    return (
      <main className="mx-auto max-w-5xl px-5 py-12">
        <div className="flex gap-2">
          <div className="h-2 w-2 rounded-full bg-field-600 animate-bounce" style={{ animationDelay: "0ms" }} />
          <div className="h-2 w-2 rounded-full bg-field-600 animate-bounce" style={{ animationDelay: "150ms" }} />
        </div>
      </main>
    );
  }

  if (!cycle) return null;

  return (
    <main className="mx-auto flex max-w-5xl flex-col gap-8 px-5 py-12">
      <header className="flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-4">
          <Link href={`/dashboard/farms/${farmId}/fields/${fieldId}/cycles/${cycleId}`} className="text-sm font-medium text-field-700 underline-offset-4 hover:underline">
            Back to {cycle.crop_name_en}
          </Link>
          <div>
            <h1 className="text-2xl font-semibold">{cycle.crop_name_en}</h1>
            <p className="text-sm text-slate-600">Scans for this crop cycle</p>
          </div>
        </div>
        <button onClick={() => signOut()} className="text-sm font-medium text-field-700 underline-offset-4 hover:underline">
          Sign out
        </button>
      </header>

      <Card>
        <h2 className="font-semibold mb-4">Start a new scan</h2>
        <Link href={`/dashboard/farms/${farmId}/fields/${fieldId}/cycles/${cycleId}/scans/new`}>
          <Button>New scan</Button>
        </Link>
        <p className="mt-3 text-sm text-slate-600">
          Take a photo of a leaf, stem, fruit, or whole plant. The system checks image quality before analyzing.
        </p>
      </Card>

      {cycleScans.length === 0 ? (
        <Card className="bg-field-50">
          <p className="text-sm text-slate-700">No scans yet. Start one above.</p>
        </Card>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2">
          {cycleScans.map((scan) => (
            <Link key={scan.id} href={`/dashboard/scans/${scan.id}`} className="block">
              <Card className="hover:border-field-400">
                <div className="flex items-start justify-between gap-4">
                  <div>
                    <h3 className="font-semibold">Scan #{scan.id.slice(0, 8)}</h3>
                    <p className="mt-1 text-sm text-slate-600">
                      {scan.plant_part} &middot; {new Date(scan.captured_at).toLocaleString()}
                    </p>
                    <p className="mt-1 text-sm text-slate-600">
                      Status: {scan.status}
                      {scan.status_reason ? ` &mdash; ${scan.status_reason}` : ""}
                    </p>
                    {scan.analysis && (
                      <p className="mt-1 text-sm text-slate-600">
                        Analysis: {scan.analysis.status}
                        {scan.analysis.primary_label_code ? ` (${scan.analysis.primary_label_code})` : ""}
                      </p>
                    )}
                  </div>
                  <Button variant="ghost" size="sm">View</Button>
                </div>
              </Card>
            </Link>
          ))}
        </div>
      )}
    </main>
  );
}
