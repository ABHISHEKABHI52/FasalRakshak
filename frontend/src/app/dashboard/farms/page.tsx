"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { api } from "@/lib/api-client";
import { useAuth } from "@/lib/auth_context";
import { Button, Card, Input } from "@/components/ui";
import type { FarmDto } from "@/types/api";

export default function FarmsPage() {
  const { token, loading, signOut } = useAuth();
  const router = useRouter();
  const [farms, setFarms] = useState<FarmDto[]>([]);
  const [name, setName] = useState("");
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    if (!loading && (!token)) {
      router.replace("/login");
    }
  }, [token, loading, router]);

  useEffect(() => {
    if (!token) return;
    let cancelled = false;
    api.farms.list(token)
      .then((data) => { if (!cancelled) setFarms(data); })
      .catch(() => {});
    return () => { cancelled = true; };
  }, [token]);

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault();
    if (!name.trim() || !token) return;
    setSubmitting(true);
    try {
      const farm = await api.farms.create(token, { name: name.trim() });
      setFarms((prev) => [farm, ...prev]);
      setName("");
    } catch {
      /* error shown via UI state if needed */
    } finally {
      setSubmitting(false);
    }
  }

  if (loading || !token) {
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
          <Link href="/dashboard" className="text-sm font-medium text-field-700 underline-offset-4 hover:underline">
            &larr; Dashboard
          </Link>
          <div>
            <h1 className="text-2xl font-semibold">Farms</h1>
            <p className="text-sm text-slate-600">{farms.length} farm{farms.length === 1 ? "" : "s"}</p>
          </div>
        </div>
        <button onClick={() => signOut()} className="text-sm font-medium text-field-700 underline-offset-4 hover:underline">
          Sign out
        </button>
      </header>

      <Card>
        <form onSubmit={handleCreate} className="flex flex-col gap-4">
          <div className="flex gap-3">
            <Input
              label="Farm name"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="e.g. Ramesh Farm"
              disabled={submitting}
              autoFocus
            />
            <Button type="submit" disabled={submitting || !name.trim()}>
              {submitting ? "Adding..." : "Add farm"}
            </Button>
          </div>
        </form>
      </Card>

      {farms.length === 0 ? (
        <Card className="bg-field-50">
          <p className="text-sm text-slate-700">No farms yet. Add one above to get started.</p>
        </Card>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2">
          {farms.map((farm) => (
            <Link key={farm.id} href={`/dashboard/farms/${farm.id}`} className="block">
              <Card className="hover:border-field-400">
                <div className="flex items-start justify-between gap-4">
                  <div>
                    <h3 className="font-semibold">{farm.name}</h3>
                    <p className="mt-1 text-sm text-slate-600">
                      {farm.field_count} {farm.field_count === 1 ? "field" : "fields"}
                      {farm.district ? ` &middot; ${farm.district}` : ""}
                      {farm.state ? ` &middot; ${farm.state}` : ""}
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
