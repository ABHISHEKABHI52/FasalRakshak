"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { api } from "@/lib/api-client";
import { useAuth } from "@/lib/auth_context";
import { Button, Card, Input } from "@/components/ui";
import type { FieldDto } from "@/types/api";

export default function FieldsPage() {
  const params = useParams();
  const router = useRouter();
  const { token, loading, signOut } = useAuth();
  const farmId = params.farmId as string;
  const [fields, setFields] = useState<FieldDto[]>([]);
  const [name, setName] = useState("");
  const [lat, setLat] = useState("");
  const [lng, setLng] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!loading && !token) { router.replace("/login"); return; }
    if (!token) return;
    let cancelled = false;
    Promise.all([
      api.farms.get(token, farmId),
      api.fields.list(token, farmId),
    ])
      .then(([, fs]) => { if (!cancelled) setFields(fs); })
      .catch(() => { if (!cancelled) router.replace("/dashboard/farms"); });
    return () => { cancelled = true; };
  }, [token, farmId, router, loading]);

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault();
    if (!name.trim() || !token) return;
    setSubmitting(true);
    setError(null);
    try {
      const body: any = { farm_id: farmId, name: name.trim() };
      if (lat && lng) body.location = { lat: parseFloat(lat), lng: parseFloat(lng) };
      const f = await api.fields.create(token, body);
      setFields((prev) => [...prev, f]);
      setName("");
      setLat("");
      setLng("");
    } catch {
      setError("Could not create field.");
    } finally {
      setSubmitting(false);
    }
  }

  if (!token) {
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
          <Link href="/dashboard/farms" className="text-sm font-medium text-field-700 underline-offset-4 hover:underline">
            Back to farms
          </Link>
          <div>
            <h1 className="text-2xl font-semibold">Fields</h1>
            <p className="text-sm text-slate-600">{fields.length} field{fields.length === 1 ? "" : "s"}</p>
          </div>
        </div>
        <button onClick={() => signOut()} className="text-sm font-medium text-field-700 underline-offset-4 hover:underline">
          Sign out
        </button>
      </header>

      <Card>
        <h2 className="font-semibold mb-4">Add field</h2>
        <form onSubmit={handleCreate} className="flex flex-col gap-4">
          <div className="grid gap-3 sm:grid-cols-3">
            <Input
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="e.g. North Plot"
              disabled={submitting}
              autoFocus
            />
            <Input
              label="Latitude"
              type="number"
              step="any"
              value={lat}
              onChange={(e) => setLat(e.target.value)}
              placeholder="24.79"
            />
            <Input
              label="Longitude"
              type="number"
              step="any"
              value={lng}
              onChange={(e) => setLng(e.target.value)}
              placeholder="85.0"
            />
          </div>
          <div className="flex gap-3">
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
          {fields.map((f) => (
            <Link key={f.id} href={`/dashboard/farms/${farmId}/fields/${f.id}`} className="block">
              <Card className="hover:border-field-400">
                <div className="flex items-start justify-between gap-4">
                  <div>
                    <h3 className="font-semibold">{f.name}</h3>
                    <p className="mt-1 text-sm text-slate-600">
                      {f.location
                        ? `At ${f.location.lat.toFixed(4)}, ${f.location.lng.toFixed(4)}`
                        : "No location set"}
                      {f.crop_cycle_count > 0
                        ? ` - ${f.crop_cycle_count} cycle${f.crop_cycle_count === 1 ? "" : "s"}`
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
