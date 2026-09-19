import Link from "next/link";

export default function NotFound() {
  return (
    <main className="mx-auto flex max-w-xl flex-col gap-4 px-5 py-16">
      <h2 className="text-xl font-semibold">Page not found</h2>
      <p className="text-sm text-slate-700">The page you are looking for does not exist in FasalRakshak.</p>
      <Link href="/" className="text-sm font-medium text-field-700 underline-offset-4 hover:underline">
        Back to home
      </Link>
    </main>
  );
}