"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { api } from "@/lib/api-client";
import { useAuth } from "@/lib/auth_context";
import { Button, Card, Input } from "@/components/ui";
import type { FieldDto, CropDto, CropCycleDto } from "@/types/api";

export default function FieldDetailPage() {
  const params = useParams();
  const router = useRouter();
  const { token, signOut } = useAuth();
  const farmId = params.farmId as string;
  const fieldId = params.fieldId as string;
  const [field, setField] = useState<FieldDto | null>(null);
  const [cycles, setCycles] = useState<CropCycleDto[]>([]);
  const [crops, setCrops] = useState<CropDto[]>([]);
  const [loading, setLoading] = useState(true);
  const [showNew, setShowNew] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [cropId, setCropId] = useState("");
  const [sowingDate, setSowingDate] = useState("");
  const [variety, setVariety] = useState("");

  useEffect(() => {
    if (!token) { router.replace("/login"); return; }
    let cancelled = false;
    Promise.all([
      api.fields.get(token, fieldId),
      api.crops.list(token),
      api.cropCycles.list(token, fieldId),
    ])
      .then(([f, cs, cy]) => {
        if (!cancelled) { setField(f); setCrops(cs); setCycles(cy); setLoading(false); }
      })
      .catch(() => { if (!cancelled) router.replace(`/dashboard/farms/${farmId}`); });
    return () => { cancelled = true; };
  }, [token, fieldId, farmId, router]);

  async function handleCreateCycle(e: React.FormEvent) {
    e.preventDefault();
    if (!cropId || !sowingDate || !token) return;
    setSubmitting(true);
    setError(null);
    try {
      const cycle = await api.cropCycles.create(token, {
        field_id: fieldId,
        crop_id: cropId,
        sowing_date: sowingDate,
        variety: variety || null,
      });
      setCycles((prev) => [cycle, ...prev]);
      setCropId("");
      setSowingDate("");
      setVariety("");
      setShowNew(false);
    } catch {
      setError("Could not create crop cycle. Try again.");
    } finally {
      setSubmitting(false);
    }
    }

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

  if (!field) return null;

  return (
    <main className="mx-auto flex max-w-5xl flex-col gap-8 px-5 py-12">
      <header className="flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-4">
          <Link href={`/dashboard/farms/${farmId}`} className="text-sm font-medium text-field-700 underline-offset-4 hover:underline">
            Back to {field.name}
          </Link>
          <div>
            <h1 className="text-2xl font-semibold">{field.name}</h1>
            <p className="text-sm text-slate-600">
              {field.location ? `At ${field.location.lat.toFixed(4)}, ${field.location.lng.toFixed(4)}` : "No location set"}
            </p>
          </div>
        </div>
        <button onClick={() => signOut()} className="text-sm font-medium text-field-700 underline-offset-4 hover:underline">
          Sign out
        </button>
      </header>

      {showNew ? (
        <Card>
          <h2 className="font-semibold mb-4">New crop cycle</h2>
          <form onSubmit={handleCreateCycle} className="flex flex-col gap-4">
            <div className="grid gap-3 sm:grid-cols-2">
              <select
                className="rounded-md border border-slate-300 bg-white px-3 py-2 text-sm"
                value={cropId}
                onChange={(e) => setCropId(e.target.value)}
                required
              >
                <option value="">Select a crop...</option>
                {crops.map((c) => (
                  <option key={c.id} value={c.id}>{c.name_en} ({c.code})</option>
                ))}
              </select>
              <Input
                label="Sowing date"
                type="date"
                value={sowingDate}
                onChange={(e) => setSowingDate(e.target.value)}
                required
              />
            </div>
            <Input
              label="Variety (optional)"
              value={variety}
              onChange={(e) => setVariety(e.target.value)}
              placeholder="e.g. Pusa Ruby"
            />
            <div className="flex gap-3">
              <Button type="submit" disabled={submitting || !cropId || !sowingDate}>
                {submitting ? "Creating..." : "Create crop cycle"}
              </Button>
              <Button type="button" variant="ghost" onClick={() => setShowNew(false)}>
                Cancel
              </Button>
            </div>
            {error ? <p className="text-sm text-red-700">{error}</p> : null}
          </form>
        </Card>
      ) : (
        <Card>
          <div className="flex items-center justify-between">
            <h2 className="font-semibold">Crop cycles</h2>
            <Button variant="secondary" onClick={() => setShowNew(true)}>
              Add cycle
            </Button>
          </div>
          {cycles.length === 0 ? (
            <p className="text-sm text-slate-700">No crop cycles yet. Add one to start scanning.</p>
          ) : (
            <div className="mt-3 grid gap-4 sm:grid-cols-2">
              {cycles.map((cycle) => (
                <Link key={cycle.id} href={`/dashboard/farms/${farmId}/fields/${fieldId}/cycles/${cycle.id}/scans`} className="block">
                  <Card className="hover:border-field-400">
                    <div className="flex items-start justify-between gap-4">
                      <div>
                        <h3 className="font-semibold">{cycle.crop_name_en}</h3>
                        <p className="mt-1 text-sm text-slate-600">
                          {cycle.crop_name_hi} - {cycle.variety || "No variety"}
                        </p>
                        <p className="mt-1 text-sm text-slate-600">
                          Sown {cycle.sowing_date} - {cycle.current_stage}
                        </p>
                        <p className="mt-1 text-sm text-slate-600">Status: {cycle.status}</p>
                      </div>
                      <Button variant="ghost" size="sm">
                        Scan
                      </Button>
                    </div>
                  </Card>
                </Link>
              ))}
            </div>
          )}
        </Card>
      )}
    </main>
  );
}
