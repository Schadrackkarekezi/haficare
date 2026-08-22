import Link from "next/link";

export default function Home() {
  return (
    <main className="flex flex-1 flex-col items-center justify-center px-4 text-center">
      <h1 className="text-3xl font-semibold text-slate-900">HafiCare</h1>
      <p className="mt-2 max-w-md text-slate-500">
        A clinic booking assistant: find the right doctor, check symptoms, and book an
        appointment — all in one chat.
      </p>
      <div className="mt-6 flex gap-3">
        <Link href="/login" className="rounded-md bg-slate-900 px-4 py-2 text-sm font-medium text-white hover:bg-slate-800">
          Log in
        </Link>
        <Link href="/signup" className="rounded-md border border-slate-300 px-4 py-2 text-sm font-medium text-slate-900 hover:bg-slate-50">
          Sign up
        </Link>
      </div>
    </main>
  );
}
