"use client";

/** Route-level error boundary (docs/05 §1.3). Never renders stack traces to the user. */

export default function GlobalError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <main className="mx-auto flex max-w-xl flex-col gap-4 px-5 py-16">
      <h2 className="text-xl font-semibold">Something went wrong</h2>
      <p className="text-sm text-slate-700">
        The page could not be displayed. Your data is safe — please try again.
      </p>
      {error.digest ? <p className="text-xs text-slate-500">Reference: {error.digest}</p> : null}
      <button
        type="button"
        onClick={reset}
        className="w-fit rounded-md bg-field-600 px-4 py-2 text-sm font-medium text-white hover:bg-field-700"
      >
        Try again
      </button>
    </main>
  );
}