export default function Loading() {
  return (
    <main className="mx-auto flex max-w-5xl flex-col gap-6 px-5 py-10" aria-busy="true">
      <div className="h-11 w-11 animate-pulse rounded-xl bg-slate-200" />
      <div className="h-8 w-2/3 animate-pulse rounded bg-slate-200" />
      <div className="h-24 animate-pulse rounded-xl bg-slate-100" />
      <div className="grid gap-4 sm:grid-cols-3">
        <div className="h-32 animate-pulse rounded-xl bg-slate-100" />
        <div className="h-32 animate-pulse rounded-xl bg-slate-100" />
        <div className="h-32 animate-pulse rounded-xl bg-slate-100" />
      </div>
      <span className="sr-only">Loading FasalRakshak…</span>
    </main>
  );
}