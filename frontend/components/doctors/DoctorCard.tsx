"use client";

import { useState } from "react";

import AvailabilitySlotPicker from "@/components/booking/AvailabilitySlotPicker";

export type DoctorRecommendation = {
  doctor_id: number;
  name: string;
  specialty: string;
  score?: number;
};

export default function DoctorCard({ doctor, onBooked }: { doctor: DoctorRecommendation; onBooked?: () => void }) {
  const [booking, setBooking] = useState(false);

  return (
    <div className="rounded-lg border border-slate-200 bg-white p-3">
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="font-medium text-slate-900">{doctor.name}</p>
          <p className="text-sm text-slate-500">{doctor.specialty}</p>
        </div>
        <button
          onClick={() => setBooking((v) => !v)}
          className="shrink-0 rounded-md border border-slate-300 px-3 py-1.5 text-sm font-medium text-slate-900 hover:bg-slate-50"
        >
          {booking ? "Close" : "View availability"}
        </button>
      </div>
      {booking && (
        <AvailabilitySlotPicker
          doctorId={doctor.doctor_id}
          doctorName={doctor.name}
          onBooked={() => {
            setBooking(false);
            onBooked?.();
          }}
        />
      )}
    </div>
  );
}
