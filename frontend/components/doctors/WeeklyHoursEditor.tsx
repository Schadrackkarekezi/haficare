"use client";

import { useEffect, useState } from "react";

type HoursEntry = { day_of_week: number; start_time: string; end_time: string };

const DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"];

export default function WeeklyHoursEditor({ doctorId, onClose }: { doctorId: number; onClose: () => void }) {
  const [rows, setRows] = useState<Record<number, { active: boolean; start: string; end: string }>>(
    Object.fromEntries(DAYS.map((_, i) => [i, { active: false, start: "09:00", end: "17:00" }]))
  );
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    // No GET-hours endpoint exists yet server-side beyond availability, so this editor
    // is write-only for now: staff set hours here, availability is derived from them.
  }, [doctorId]);

  function toggleDay(day: number) {
    setRows((prev) => ({ ...prev, [day]: { ...prev[day], active: !prev[day].active } }));
  }

  function updateTime(day: number, field: "start" | "end", value: string) {
    setRows((prev) => ({ ...prev, [day]: { ...prev[day], [field]: value } }));
  }

  async function save() {
    setSaving(true);
    setError(null);
    const hours: HoursEntry[] = Object.entries(rows)
      .filter(([, r]) => r.active)
      .map(([day, r]) => ({ day_of_week: Number(day), start_time: r.start, end_time: r.end }));

    try {
      const res = await fetch(`/api/doctors/${doctorId}/weekly-hours`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ hours }),
      });
      if (!res.ok) {
        const data = await res.json();
        setError(data.error ?? "Couldn't save hours.");
        return;
      }
      onClose();
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="mt-3 rounded-md border border-slate-200 bg-slate-50 p-4">
      <p className="mb-3 text-sm font-medium text-slate-700">Weekly availability</p>
      <div className="space-y-2">
        {DAYS.map((label, day) => {
          const row = rows[day];
          return (
            <div key={day} className="flex items-center gap-3 text-sm">
              <label className="flex w-32 items-center gap-2">
                <input type="checkbox" checked={row.active} onChange={() => toggleDay(day)} />
                {label}
              </label>
              <input
                type="time"
                disabled={!row.active}
                value={row.start}
                onChange={(e) => updateTime(day, "start", e.target.value)}
                className="rounded border border-slate-300 px-2 py-1 disabled:opacity-40"
              />
              <span className="text-slate-400">to</span>
              <input
                type="time"
                disabled={!row.active}
                value={row.end}
                onChange={(e) => updateTime(day, "end", e.target.value)}
                className="rounded border border-slate-300 px-2 py-1 disabled:opacity-40"
              />
            </div>
          );
        })}
      </div>

      {error && <p className="mt-2 text-sm text-red-600">{error}</p>}

      <div className="mt-4 flex gap-2">
        <button
          onClick={save}
          disabled={saving}
          className="rounded-md bg-slate-900 px-3 py-1.5 text-sm font-medium text-white hover:bg-slate-800 disabled:opacity-50"
        >
          {saving ? "Saving…" : "Save hours"}
        </button>
        <button onClick={onClose} className="rounded-md px-3 py-1.5 text-sm text-slate-600 hover:bg-slate-100">
          Cancel
        </button>
      </div>
    </div>
  );
}
