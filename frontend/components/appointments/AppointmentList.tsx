"use client";

import { useState } from "react";

export type AppointmentRow = {
  appointment_id: number;
  doctor_name: string;
  patient_name: string;
  date: string;
  time_slot: string;
  status: string;
};

export default function AppointmentList({
  initialAppointments,
  showPatientColumn,
}: {
  initialAppointments: AppointmentRow[];
  showPatientColumn: boolean;
}) {
  const [appointments, setAppointments] = useState(initialAppointments);
  const [cancellingId, setCancellingId] = useState<number | null>(null);

  async function cancel(id: number) {
    setCancellingId(id);
    try {
      const res = await fetch(`/api/appointments/${id}/cancel`, { method: "POST" });
      if (res.ok) {
        setAppointments((prev) =>
          prev.map((a) => (a.appointment_id === id ? { ...a, status: "cancelled" } : a))
        );
      }
    } finally {
      setCancellingId(null);
    }
  }

  const upcoming = appointments.filter((a) => a.status === "booked");
  const past = appointments.filter((a) => a.status !== "booked");

  if (appointments.length === 0) {
    return <p className="text-sm text-slate-500">No appointments yet.</p>;
  }

  return (
    <div className="space-y-8">
      <Section
        title="Upcoming"
        rows={upcoming}
        showPatientColumn={showPatientColumn}
        onCancel={cancel}
        cancellingId={cancellingId}
      />
      <Section title="Past / cancelled" rows={past} showPatientColumn={showPatientColumn} />
    </div>
  );
}

function Section({
  title,
  rows,
  showPatientColumn,
  onCancel,
  cancellingId,
}: {
  title: string;
  rows: AppointmentRow[];
  showPatientColumn: boolean;
  onCancel?: (id: number) => void;
  cancellingId?: number | null;
}) {
  return (
    <div>
      <h2 className="mb-2 text-sm font-medium text-slate-700">{title}</h2>
      {rows.length === 0 ? (
        <p className="text-sm text-slate-400">Nothing here.</p>
      ) : (
        <div className="overflow-x-auto rounded-lg border border-slate-200">
          <table className="w-full text-sm">
            <thead className="bg-slate-50 text-left text-slate-500">
              <tr>
                <th className="px-3 py-2">Doctor</th>
                {showPatientColumn && <th className="px-3 py-2">Patient</th>}
                <th className="px-3 py-2">Date</th>
                <th className="px-3 py-2">Time</th>
                <th className="px-3 py-2">Status</th>
                {onCancel && <th className="px-3 py-2" />}
              </tr>
            </thead>
            <tbody>
              {rows.map((a) => (
                <tr key={a.appointment_id} className="border-t border-slate-100">
                  <td className="px-3 py-2">{a.doctor_name}</td>
                  {showPatientColumn && <td className="px-3 py-2">{a.patient_name}</td>}
                  <td className="px-3 py-2">{a.date}</td>
                  <td className="px-3 py-2">{a.time_slot}</td>
                  <td className="px-3 py-2 capitalize">{a.status}</td>
                  {onCancel && (
                    <td className="px-3 py-2 text-right">
                      <button
                        onClick={() => onCancel(a.appointment_id)}
                        disabled={cancellingId === a.appointment_id}
                        className="text-red-600 hover:text-red-800 disabled:opacity-50"
                      >
                        Cancel
                      </button>
                    </td>
                  )}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
