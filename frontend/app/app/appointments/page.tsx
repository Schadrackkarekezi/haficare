import AppointmentList, { AppointmentRow } from "@/components/appointments/AppointmentList";
import { apiFetch } from "@/lib/apiClient";
import { getServerToken } from "@/lib/auth";

export default async function PatientAppointmentsPage() {
  const token = await getServerToken();
  const appointments = await apiFetch<AppointmentRow[]>("/appointments", { token });

  return (
    <div>
      <h1 className="text-xl font-semibold text-slate-900">My Appointments</h1>
      <div className="mt-6">
        <AppointmentList initialAppointments={appointments} showPatientColumn={false} />
      </div>
    </div>
  );
}
