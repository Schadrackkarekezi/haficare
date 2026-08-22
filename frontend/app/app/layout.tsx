import Link from "next/link";

import LogoutButton from "@/components/LogoutButton";

export default function PatientAppLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex flex-1 flex-col">
      <header className="border-b border-slate-200">
        <div className="mx-auto flex max-w-3xl items-center justify-between px-4 py-3">
          <div className="flex items-center gap-6">
            <span className="font-semibold text-slate-900">HafiCare</span>
            <nav className="flex gap-4 text-sm text-slate-600">
              <Link href="/app/chat" className="hover:text-slate-900">
                Chat
              </Link>
              <Link href="/app/appointments" className="hover:text-slate-900">
                My Appointments
              </Link>
            </nav>
          </div>
          <LogoutButton />
        </div>
      </header>
      <main className="mx-auto flex w-full max-w-3xl flex-1 flex-col px-4 py-6">{children}</main>
    </div>
  );
}
