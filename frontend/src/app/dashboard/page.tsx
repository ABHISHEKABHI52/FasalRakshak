"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { api } from "@/lib/api-client";
import { useAuth } from "@/lib/auth_context";
import { Card } from "@/components/ui";
import type { FarmDto } from "@/types/api";

export default function DashboardPage() {
  const { user, token, loading, signOut } = useAuth();
  const router = useRouter();
  const [, setFarms] = useState<FarmDto[]>([]);

  useEffect(() => {
    if (!loading && (!user || !token)) {
      router.replace("/login");
    }
  }, [user, token, loading, router]);

  useEffect(() => {
    if (!token) return;
    let cancelled = false;
    api.farms.list(token)
      .then((data) => { if (!cancelled) setFarms(data); })
      .catch(() => {});
    return () => { cancelled = true; };
  }, [token]);

  if (loading || (!user && !token)) {
    return (
      <main className="mx-auto flex max-w-lg flex-col gap-6 px-5 py-12">
        <div className="flex gap-2">
          <div className="h-2 w-2 rounded-full bg-field-600 animate-bounce" style={{ animationDelay: "0ms" }} />
          <div className="h-2 w-2 rounded-full bg-field-600 animate-bounce" style={{ animationDelay: "150ms" }} />
          <div className="h-2 w-2 rounded-full bg-field-600 animate-bounce" style={{ animationDelay: "300ms" }} />
        </div>
      </main>
    );
  }

  return (
    <main className="mx-auto flex max-w-5xl flex-col gap-8 px-5 py-12">
      <header className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold">My Dashboard</h1>
          <p className="text-sm text-slate-600">{user?.full_name} &middot; {user?.phone}</p>
        </div>
        <button onClick={() => signOut()} className="text-sm font-medium text-field-700 underline-offset-4 hover:underline">
          Sign out
        </button>
      </header>

      <div className="grid gap-6 sm:grid-cols-2">
        <Link href="/dashboard/farms" className="block">
          <Card className="h-full hover:border-field-400">
            <div className="flex items-start gap-4">
              <span className="mt-1 grid h-10 w-10 place-items-center rounded-lg bg-field-100 text-field-700 text-lg">&#127807;</span>
              <div>
                <h2 className="font-semibold">Farms</h2>
                <p className="mt-1 text-sm text-slate-600">Manage your farms, fields and crop cycles.</p>
                <span className="mt-2 inline-block text-sm font-medium text-field-700">Manage farms &rarr;</span>
              </div>
            </div>
          </Card>
        </Link>

        <Link href="/dashboard/scans" className="block">
          <Card className="h-full hover:border-field-400">
            <div className="flex items-start gap-4">
              <span className="mt-1 grid h-10 w-10 place-items-center rounded-lg bg-field-100 text-field-700 text-lg">&#128202;</span>
              <div>
                <h2 className="font-semibold">Scan History</h2>
                <p className="mt-1 text-sm text-slate-600">Review your crop scans and results.</p>
                <span className="mt-2 inline-block text-sm font-medium text-field-700">View scans &rarr;</span>
              </div>
            </div>
          </Card>
        </Link>
      </div>

      <Card className="bg-field-50">
        <h2 className="font-semibold">How FasalRakshak works</h2>
        <p className="mt-2 text-sm text-slate-700">
          Create a farm, add fields with locations, start a crop cycle for a supported crop, then capture leaf scans.
          Each image passes an image-quality gate before any analysis runs. When visual evidence is insufficient, the
          system says so rather than guessing a disease name.
        </p>
      </Card>
    </main>
  );
}
