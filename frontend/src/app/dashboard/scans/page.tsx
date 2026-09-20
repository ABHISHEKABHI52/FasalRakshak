"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { api } from "@/lib/api-client";
import { useAuth } from "@/lib/auth_context";
import { Button, Card } from "@/components/ui";
import type { ScanDto } from "@/types/api";

export default function ScanHistoryPage() {
  const router = useRouter();
  const { token, signOut } = useAuth();
  const [scans, setScans] = useState<ScanDto[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!token) { router.replace("/login"); return; }
    let cancelled = false;
    api.scans.list(token)
      .then((data) => { if (!cancelled) { setScans(data.items); setLoading(false); } })
      .catch(() => { if (!cancelled) { setLoading(false); } });
    return () => { cancelled = true; };
  }, [token, router]);

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
        <div>
          <h1 className="text-2xl font-semibold">Scan History</h1>
          <p className="text-sm text-slate-600">{scans.length} scan{scans.length === 1 ? "" : "s"}</p>
        </div>
        <button onClick={() => signOut()} className="text-sm font-medium text-field-700 underline-offset-4 hover:underline">
          Sign out
        </button>
      </header>

      {scans.length === 0 ? (
        <Card className="bg-field-50">
          <p className="text-sm text-slate-700">No scans yet. Start by creating a farm, then a field, then a crop cycle.</p>
          <Link href="/dashboard/farms" className="mt-3 inline-block">
            <Button>Go to farms</Button>
          </Link>
        </Card>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2">
          {scans.map((scan) => (
            <Link key={scan.id} href={`/dashboard/scans/${scan.id}`} className="block">
              <Card className="hover:border-field-400">
                <div className="flex items-start justify-between gap-4">
                  <div>
                    <h3 className="font-semibold">Scan #{scan.id.slice(0, 8)}</h3>
                    <p className="mt-1 text-sm text-slate-600">{scan.plant_part}</p>
                    <p className="mt-1 text-sm text-slate-600">
                      {new Date(scan.captured_at).toLocaleString()}
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
