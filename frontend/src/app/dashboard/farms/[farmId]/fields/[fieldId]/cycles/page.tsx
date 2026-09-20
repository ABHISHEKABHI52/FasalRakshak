"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { api } from "@/lib/api-client";
import { useAuth } from "@/lib/auth_context";
import { Button, Card } from "@/components/ui";
import type { CropCycleDto } from "@/types/api";

export default function CyclesPage() {
  const params = useParams();
  const router = useRouter();
  const { token, signOut } = useAuth();
  const farmId = params.farmId as string;
  const fieldId = params.fieldId as string;
  const [cycles, setCycles] = useState<CropCycleDto[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!token) { router.replace("/login"); return; }
    let cancelled = false;
    api.cropCycles.list(token, fieldId)
      .then((cs) => { if (!cancelled) { setCycles(cs); setLoading(false); } })
      .catch(() => { if (!cancelled) router.replace(`/dashboard/farms/${farmId}`); });
    return () => { cancelled = true; };
  }, [token, fieldId, farmId, router]);

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

  return (
    <main className="mx-auto flex max-w-5xl flex-col gap-8 px-5 py-12">
      <header className="flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-4">
          <Link href={`/dashboard/farms/${farmId}/fields/${fieldId}`} className="text-sm font-medium text-field-700 underline-offset-4 hover:underline">
            Back to fields
          </Link>
          <div>
            <h1 className="text-2xl font-semibold">Crop Cycles</h1>
            <p className="text-sm text-slate-600">{cycles.length} cycle{cycles.length === 1 ? "" : "s"}</p>
          </div>
        </div>
        <button onClick={() => signOut()} className="text-sm font-medium text-field-700 underline-offset-4 hover:underline">
          Sign out
        </button>
      </header>

      {cycles.length === 0 ? (
        <Card className="bg-field-50">
          <p className="text-sm text-slate-700">No crop cycles yet. Go back and create one.</p>
        </Card>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2">
          {cycles.map((cycle) => (
            <Link key={cycle.id} href={`/dashboard/farms/${farmId}/fields/${fieldId}/cycles/${cycle.id}/scans`} className="block">
              <Card className="hover:border-field-400">
                <div className="flex items-start justify-between gap-4">
                  <div>
                    <h3 className="font-semibold">{cycle.crop_name_en}</h3>
                    <p className="mt-1 text-sm text-slate-600">
                      {cycle.crop_name_hi} &middot; {cycle.variety || "No variety"}
                    </p>
                    <p className="mt-1 text-sm text-slate-600">
                      Sown {cycle.sowing_date} &middot; {cycle.current_stage}
                    </p>
                    <p className="mt-1 text-sm text-slate-600">
                      Status: {cycle.status}
                    </p>
                  </div>
                  <Button variant="ghost" size="sm">Scan</Button>
                </div>
              </Card>
            </Link>
          ))}
        </div>
      )}
    </main>
  );
}
