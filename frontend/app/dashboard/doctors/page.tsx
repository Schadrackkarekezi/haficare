"use client";

import { useEffect, useState } from "react";

import WeeklyHoursEditor from "@/components/doctors/WeeklyHoursEditor";

type Doctor = { id: number; name: string; specialty: string; bio: string; is_active: boolean };

export default function DoctorsPage() {
  const [doctors, setDoctors] = useState<Doctor[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [editingHoursFor, setEditingHoursFor] = useState<number | null>(null);

  const [name, setName] = useState("");
  const [specialty, setSpecialty] = useState("");
  const [bio, setBio] = useState("");
  const [creating, setCreating] = useState(false);

  async function loadDoctors() {
    setLoading(true);
    try {
      const res = await fetch("/api/doctors");
      const data = await res.json();
      setDoctors(data);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    // Initial fetch-on-mount; loadDoctors() is also called imperatively after
    // add/remove/hours actions below, so it can't be restructured as a plain
    // effect body without duplicating that logic.
    // eslint-disable-next-line react-hooks/set-state-in-effect
    loadDoctors();
  }, []);

  async function addDoctor(e: React.FormEvent) {
    e.preventDefault();
    setCreating(true);
    setError(null);
    try {
      const res = await fetch("/api/doctors", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name, specialty, bio }),
      });
      const data = await res.json();
      if (!res.ok) {
        setError(data.error ?? "Couldn't add doctor.");
        return;
      }
      setName("");
      setSpecialty("");
      setBio("");
      await loadDoctors();
    } finally {
      setCreating(false);
    }
  }

  async function removeDoctor(id: number) {
    if (!confirm("Remove this doctor from your roster?")) return;
    await fetch(`/api/doctors/${id}`, { method: "DELETE" });
    await loadDoctors();
  }

  return (
    <div>
      <h1 className="text-xl font-semibold text-slate-900">Doctors</h1>

      <form onSubmit={addDoctor} className="mt-6 grid grid-cols-1 gap-3 rounded-lg border border-slate-200 p-4 sm:grid-cols-4">
        <input
          placeholder="Name"
          required
          value={name}
          onChange={(e) => setName(e.target.value)}
          className="rounded-md border border-slate-300 px-3 py-2 text-sm sm:col-span-1"
        />
        <input
          placeholder="Specialty"
          required
          value={specialty}
          onChange={(e) => setSpecialty(e.target.value)}
          className="rounded-md border border-slate-300 px-3 py-2 text-sm sm:col-span-1"
        />
        <input
          placeholder="Short bio (used for matching patients to this doctor)"
          required
          value={bio}
          onChange={(e) => setBio(e.target.value)}
          className="rounded-md border border-slate-300 px-3 py-2 text-sm sm:col-span-1"
        />
        <button
          type="submit"
          disabled={creating}
          className="rounded-md bg-slate-900 px-3 py-2 text-sm font-medium text-white hover:bg-slate-800 disabled:opacity-50"
        >
          {creating ? "Adding…" : "Add doctor"}
        </button>
      </form>
      {error && <p className="mt-2 text-sm text-red-600">{error}</p>}

      <div className="mt-6 space-y-3">
        {loading && <p className="text-sm text-slate-500">Loading…</p>}
        {!loading && doctors.length === 0 && <p className="text-sm text-slate-500">No doctors yet.</p>}
        {doctors.map((d) => (
          <div key={d.id} className="rounded-lg border border-slate-200 p-4">
            <div className="flex items-start justify-between">
              <div>
                <p className="font-medium text-slate-900">{d.name}</p>
                <p className="text-sm text-slate-500">{d.specialty}</p>
                <p className="mt-1 text-sm text-slate-600">{d.bio}</p>
              </div>
              <div className="flex shrink-0 gap-3 text-sm">
                <button
                  onClick={() => setEditingHoursFor(editingHoursFor === d.id ? null : d.id)}
                  className="text-slate-600 hover:text-slate-900"
                >
                  {editingHoursFor === d.id ? "Close" : "Set hours"}
                </button>
                <button onClick={() => removeDoctor(d.id)} className="text-red-600 hover:text-red-800">
                  Remove
                </button>
              </div>
            </div>
            {editingHoursFor === d.id && (
              <WeeklyHoursEditor doctorId={d.id} onClose={() => setEditingHoursFor(null)} />
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
