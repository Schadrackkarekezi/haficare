"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";

type Clinic = { slug: string; name: string; city: string | null };

export default function SignupPage() {
  const router = useRouter();
  const [mode, setMode] = useState<"clinic" | "patient">("clinic");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  const [clinicName, setClinicName] = useState("");
  const [clinicCity, setClinicCity] = useState("");

  const [clinics, setClinics] = useState<Clinic[]>([]);
  const [clinicSlug, setClinicSlug] = useState("");

  useEffect(() => {
    if (mode !== "patient") return;
    fetch("/api/clinics")
      .then((r) => r.json())
      .then((data: Clinic[]) => {
        setClinics(data);
        if (data.length > 0) setClinicSlug(data[0].slug);
      })
      .catch(() => setClinics([]));
  }, [mode]);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      const path = mode === "clinic" ? "/api/auth/signup/clinic" : "/api/auth/signup/patient";
      const body =
        mode === "clinic"
          ? { clinic_name: clinicName, clinic_city: clinicCity || null, full_name: fullName, email, password }
          : { clinic_slug: clinicSlug, full_name: fullName, email, password };

      const res = await fetch(path, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      const data = await res.json();
      if (!res.ok) {
        setError(data.error ?? "Sign up failed.");
        return;
      }
      router.push(data.role === "staff" ? "/dashboard" : "/app");
      router.refresh();
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="flex flex-1 items-center justify-center px-4 py-10">
      <div className="w-full max-w-sm">
        <h1 className="mb-1 text-2xl font-semibold text-slate-900">Create your HafiCare account</h1>

        <div className="mb-6 mt-4 flex rounded-md border border-slate-300 p-1 text-sm">
          <button
            type="button"
            onClick={() => setMode("clinic")}
            className={`flex-1 rounded px-3 py-1.5 ${mode === "clinic" ? "bg-slate-900 text-white" : "text-slate-600"}`}
          >
            Register a clinic
          </button>
          <button
            type="button"
            onClick={() => setMode("patient")}
            className={`flex-1 rounded px-3 py-1.5 ${mode === "patient" ? "bg-slate-900 text-white" : "text-slate-600"}`}
          >
            Join as a patient
          </button>
        </div>

        <form onSubmit={onSubmit} className="space-y-4">
          {mode === "clinic" && (
            <>
              <div>
                <label className="mb-1 block text-sm font-medium text-slate-700">Clinic name</label>
                <input
                  required
                  value={clinicName}
                  onChange={(e) => setClinicName(e.target.value)}
                  className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:border-slate-500 focus:outline-none"
                />
              </div>
              <div>
                <label className="mb-1 block text-sm font-medium text-slate-700">City (optional)</label>
                <input
                  value={clinicCity}
                  onChange={(e) => setClinicCity(e.target.value)}
                  className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:border-slate-500 focus:outline-none"
                />
              </div>
            </>
          )}

          {mode === "patient" && (
            <div>
              <label className="mb-1 block text-sm font-medium text-slate-700">Your clinic</label>
              {clinics.length === 0 ? (
                <p className="text-sm text-slate-500">No clinics have registered yet.</p>
              ) : (
                <select
                  value={clinicSlug}
                  onChange={(e) => setClinicSlug(e.target.value)}
                  className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:border-slate-500 focus:outline-none"
                >
                  {clinics.map((c) => (
                    <option key={c.slug} value={c.slug}>
                      {c.name}
                      {c.city ? ` — ${c.city}` : ""}
                    </option>
                  ))}
                </select>
              )}
            </div>
          )}

          <div>
            <label className="mb-1 block text-sm font-medium text-slate-700">
              {mode === "clinic" ? "Your name" : "Full name"}
            </label>
            <input
              required
              value={fullName}
              onChange={(e) => setFullName(e.target.value)}
              className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:border-slate-500 focus:outline-none"
            />
          </div>
          <div>
            <label className="mb-1 block text-sm font-medium text-slate-700">Email</label>
            <input
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:border-slate-500 focus:outline-none"
            />
          </div>
          <div>
            <label className="mb-1 block text-sm font-medium text-slate-700">Password</label>
            <input
              type="password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:border-slate-500 focus:outline-none"
            />
          </div>

          {error && <p className="text-sm text-red-600">{error}</p>}

          <button
            type="submit"
            disabled={loading || (mode === "patient" && clinics.length === 0)}
            className="w-full rounded-md bg-slate-900 px-3 py-2 text-sm font-medium text-white hover:bg-slate-800 disabled:opacity-50"
          >
            {loading ? "Creating account…" : "Sign up"}
          </button>
        </form>

        <p className="mt-6 text-sm text-slate-500">
          Already have an account?{" "}
          <Link href="/login" className="font-medium text-slate-900 underline">
            Log in
          </Link>
        </p>
      </div>
    </main>
  );
}
