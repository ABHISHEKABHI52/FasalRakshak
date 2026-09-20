"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { api } from "@/lib/api-client";
import { useAuth } from "@/lib/auth_context";
import { Button, Card } from "@/components/ui";
import type { FarmDto, FieldDto } from "@/types/api";

export default function FarmDetailPage() {
  const params = useParams();
  const router = useRouter();
  const { token, signOut } = useAuth();
  const farmId = params.farmId as string;
  const [farm, setFarm] = useState<FarmDto | null>(null);
  const [fields, setFields] = useState<FieldDto[]>([]);
  const [loading, setLoading] = useState(true);
  const [name, setName] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!token) { router.replace("/login"); return; }
    let cancelled = false;
    Promise.all([
      api.farms.get(token, farmId),
      api.fields.list(token, farmId),
    ])
      .then(([f, fs]) => {
        if (!cancelled) { setFarm(f); setFields(fs); setLoading(false); }
      })
      .catch(() => { if (!cancelled) router.replace("/dashboard/farms"); });
    return () => { cancelled = true; };
  }, [token, farmId, router]);

  async function handleCreateField(e: React.FormEvent) {
    e.preventDefault();
    if (!name.trim() || !token) return;
    setSubmitting(true);
    setError(null);
    try {
      const field = await api.fields.create(token, { farm_id: farmId, name: name.trim() });
      setFields((prev) => [...prev, field]);
      setName("");
    } catch {
      setError("Could not create field.");
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

  if (!farm) return null;

  return (
    <main className="mx-auto flex max-w-5xl flex-col gap-8 px-5 py-12">
      <header className="flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-4">
          <Link href="/dashboard/farms" className="text-sm font-medium text-field-700 underline-offset-4 hover:underline">
            Back to farms
          </Link>
          <div>
            <h1 className="text-2xl font-semibold">{farm.name}</h1>
            <p className="text-sm text-slate-600">
              {fields.length} {fields.length === 1 ? "field" : "fields"}
              {farm.district ? ` - ${farm.district}` : ""}
              {farm.state ? ` - ${farm.state}` : ""}
            </p>
          </div>
        </div>
        <button onClick={() => signOut()} className="text-sm font-medium text-field-700 underline-offset-4 hover:underline">
          Sign out
        </button>
      </header>

      <Card>
        <h2 className="font-semibold mb-4">Add field</h2>
        <form onSubmit={handleCreateField} className="flex flex-col gap-4">
          <div className="flex gap-3">
            <input
              className="rounded-md border border-slate-300 bg-white px-3 py-2 text-sm"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="e.g. North Plot"
              disabled={submitting}
              autoFocus
            />
            <Button type="submit" disabled={submitting || !name.trim()}>
              {submitting ? "Adding..." : "Add field"}
            </Button>
          </div>
          {error ? <p className="text-sm text-red-700">{error}</p> : null}
        </form>
      </Card>

      {fields.length === 0 ? (
        <Card className="bg-field-50">
          <p className="text-sm text-slate-700">No fields yet. Add one above.</p>
        </Card>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2">
          {fields.map((field) => (
            <Link key={field.id} href={`/dashboard/farms/${farmId}/fields/${field.id}`} className="block">
              <Card className="hover:border-field-400">
                <div className="flex items-start justify-between gap-4">
                  <div>
                    <h3 className="font-semibold">{field.name}</h3>
                    <p className="mt-1 text-sm text-slate-600">
                      {field.location
                        ? `At ${field.location.lat.toFixed(4)}, ${field.location.lng.toFixed(4)}`
                        : "No location set"}
                      {field.crop_cycle_count > 0
                        ? ` - ${field.crop_cycle_count} cycle${field.crop_cycle_count === 1 ? "" : "s"}`
                        : ""}
                    </p>
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
