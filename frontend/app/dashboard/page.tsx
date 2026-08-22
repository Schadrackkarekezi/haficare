import { apiFetch } from "@/lib/apiClient";
import { getServerToken } from "@/lib/auth";

type Doctor = { id: number; name: string; specialty: string; bio: string; is_active: boolean };
type Appointment = { appointment_id: number; status: string };

export default async function DashboardOverviewPage() {
  const token = await getServerToken();
  const [doctors, appointments] = await Promise.all([
    apiFetch<Doctor[]>("/doctors", { token }),
    apiFetch<Appointment[]>("/appointments", { token }),
  ]);
  const upcoming = appointments.filter((a) => a.status === "booked").length;

  return (
    <div>
      <h1 className="text-xl font-semibold text-slate-900">Overview</h1>
      <div className="mt-6 grid grid-cols-2 gap-4 sm:grid-cols-3">
        <Stat label="Doctors" value={doctors.length} />
        <Stat label="Upcoming appointments" value={upcoming} />
        <Stat label="Total appointments" value={appointments.length} />
      </div>
    </div>
  );
}

function Stat({ label, value }: { label: string; value: number }) {
  return (
    <div className="rounded-lg border border-slate-200 p-4">
      <p className="text-2xl font-semibold text-slate-900">{value}</p>
      <p className="text-sm text-slate-500">{label}</p>
    </div>
  );
}
