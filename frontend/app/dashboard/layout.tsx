import Link from "next/link";

import LogoutButton from "@/components/LogoutButton";

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex flex-1 flex-col">
      <header className="border-b border-slate-200">
        <div className="mx-auto flex max-w-4xl items-center justify-between px-4 py-3">
          <div className="flex items-center gap-6">
            <span className="font-semibold text-slate-900">HafiCare · Staff</span>
            <nav className="flex gap-4 text-sm text-slate-600">
              <Link href="/dashboard" className="hover:text-slate-900">
                Overview
              </Link>
              <Link href="/dashboard/doctors" className="hover:text-slate-900">
                Doctors
              </Link>
              <Link href="/dashboard/appointments" className="hover:text-slate-900">
                Appointments
              </Link>
            </nav>
          </div>
          <LogoutButton />
        </div>
      </header>
      <main className="mx-auto w-full max-w-4xl flex-1 px-4 py-8">{children}</main>
    </div>
  );
}
