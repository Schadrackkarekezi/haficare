"use client";

import { useState } from "react";

function today(): string {
  return new Date().toISOString().slice(0, 10);
}

export default function AvailabilitySlotPicker({
  doctorId,
  doctorName,
  onBooked,
}: {
  doctorId: number;
  doctorName: string;
  onBooked: () => void;
}) {
  const [date, setDate] = useState(today());
  const [slots, setSlots] = useState<string[]>([]);
  const [loadingSlots, setLoadingSlots] = useState(false);
  const [selectedSlot, setSelectedSlot] = useState<string | null>(null);
  const [contact, setContact] = useState("");
  const [booking, setBooking] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [confirmed, setConfirmed] = useState(false);

  async function loadSlots(newDate: string) {
    setDate(newDate);
    setSelectedSlot(null);
    setLoadingSlots(true);
    setError(null);
    try {
      const res = await fetch(`/api/doctors/${doctorId}/availability?date=${newDate}`);
      const data = await res.json();
      setSlots(data.slots ?? []);
    } finally {
      setLoadingSlots(false);
    }
  }

  async function confirmBooking() {
    if (!selectedSlot) return;
    setBooking(true);
    setError(null);
    try {
      const res = await fetch("/api/appointments", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ doctor_id: doctorId, date, time_slot: selectedSlot, contact }),
      });
      const data = await res.json();
      if (!res.ok) {
        setError(data.error ?? "Couldn't book that slot.");
        return;
      }
      setConfirmed(true);
      setTimeout(onBooked, 1200);
    } finally {
      setBooking(false);
    }
  }

  if (confirmed) {
    return (
      <p className="mt-3 rounded-md bg-green-50 px-3 py-2 text-sm text-green-700">
        Booked with {doctorName} on {date} at {selectedSlot}.
      </p>
    );
  }

  return (
    <div className="mt-3 rounded-md border border-slate-200 bg-slate-50 p-3">
      <div className="flex items-center gap-2">
        <label className="text-sm text-slate-600">Date</label>
        <input
          type="date"
          value={date}
          min={today()}
          onChange={(e) => loadSlots(e.target.value)}
          className="rounded border border-slate-300 px-2 py-1 text-sm"
        />
      </div>

      <div className="mt-3">
        {loadingSlots && <p className="text-sm text-slate-500">Loading availability…</p>}
        {!loadingSlots && slots.length === 0 && (
          <p className="text-sm text-slate-500">No open slots that day.</p>
        )}
        {!loadingSlots && slots.length > 0 && (
          <div className="flex flex-wrap gap-2">
            {slots.map((slot) => (
              <button
                key={slot}
                onClick={() => setSelectedSlot(slot)}
                className={`rounded-md border px-3 py-1 text-sm ${
                  selectedSlot === slot
                    ? "border-slate-900 bg-slate-900 text-white"
                    : "border-slate-300 text-slate-700 hover:bg-white"
                }`}
              >
                {slot}
              </button>
            ))}
          </div>
        )}
      </div>

      {selectedSlot && (
        <div className="mt-3 flex flex-wrap items-center gap-2">
          <input
            type="text"
            required
            placeholder="Phone or email for confirmation"
            value={contact}
            onChange={(e) => setContact(e.target.value)}
            className="rounded border border-slate-300 px-2 py-1 text-sm"
          />
          <button
            onClick={confirmBooking}
            disabled={booking || !contact}
            className="rounded-md bg-slate-900 px-3 py-1.5 text-sm font-medium text-white hover:bg-slate-800 disabled:opacity-50"
          >
            {booking ? "Booking…" : `Confirm ${selectedSlot}`}
          </button>
        </div>
      )}

      {error && <p className="mt-2 text-sm text-red-600">{error}</p>}
    </div>
  );
}
