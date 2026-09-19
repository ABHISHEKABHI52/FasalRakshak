"use client";

/**
 * Sign-in page — proves the API client + error mapping against the real backend.
 *
 * Phase 1 scope: authentication-ready shell. Session persistence, protected
 * farmer routes and token-refresh handling are TODO — FUTURE PHASE (Phase 2),
 * per docs/IMPLEMENTATION_STATUS.md. The access token is intentionally kept
 * in memory only (docs/12 §1: no tokens in localStorage).
 */

import Link from "next/link";
import { useState, type FormEvent } from "react";

import { Button, Card } from "@/components/ui";
import { ApiError, api } from "@/lib/api-client";
import { friendlyMessage } from "@/lib/error-messages";
import type { UserDto } from "@/types/api";

export default function LoginPage() {
  const [identifier, setIdentifier] = useState("");
  const [password, setPassword] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [user, setUser] = useState<UserDto | null>(null);

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setBusy(true);
    setError(null);
    try {
      const result = await api.auth.login({ phone_or_email: identifier.trim(), password });
      setUser(result.user);
    } catch (err) {
      setError(friendlyMessage(err instanceof ApiError ? err : null));
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="mx-auto flex max-w-md flex-col gap-6 px-5 py-12">
      <header className="flex flex-col gap-1">
        <h1 className="text-2xl font-semibold">Sign in to FasalRakshak</h1>
        <p className="text-sm text-slate-600">Scan. Predict. Protect.</p>
      </header>

      {user ? (
        <Card className="bg-field-50">
          <h2 className="font-semibold">Signed in</h2>
          <p className="mt-1 text-sm text-slate-700">
            {user.full_name} · {user.phone}
          </p>
          <p className="mt-1 text-sm text-slate-700">Roles: {user.roles.join(", ")}</p>
          <p className="mt-3 text-xs text-slate-600">
            TODO — FUTURE PHASE: farmer dashboard, session persistence and protected routes (Phase 2).
          </p>
        </Card>
      ) : (
        <Card>
          <form className="flex flex-col gap-4" onSubmit={onSubmit} noValidate>
            <label className="flex flex-col gap-1 text-sm">
              <span className="font-medium">Phone number</span>
              <input
                className="rounded-md border border-slate-300 px-3 py-2"
                type="tel"
                inputMode="tel"
                autoComplete="username"
                placeholder="+919876543210"
                value={identifier}
                onChange={(event) => setIdentifier(event.target.value)}
                required
              />
            </label>
            <label className="flex flex-col gap-1 text-sm">
              <span className="font-medium">Password</span>
              <input
                className="rounded-md border border-slate-300 px-3 py-2"
                type="password"
                autoComplete="current-password"
                value={password}
                onChange={(event) => setPassword(event.target.value)}
                required
              />
            </label>

            {error ? (
              <p role="alert" className="rounded-md bg-red-50 px-3 py-2 text-sm text-red-800">
                {error}
              </p>
            ) : null}

            <Button type="submit" disabled={busy}>
              {busy ? "Signing in…" : "Sign in"}
            </Button>
          </form>
          <p className="mt-4 text-xs text-slate-600">
            Registration in the app arrives with farmer onboarding (Phase 2). The API already supports
            <code className="mx-1 rounded bg-slate-100 px-1">POST /api/v1/auth/register</code>.
          </p>
        </Card>
      )}

      <Link href="/" className="text-sm font-medium text-field-700 underline-offset-4 hover:underline">
        Back to home
      </Link>
    </main>
  );
}