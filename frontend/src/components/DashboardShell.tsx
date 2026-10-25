"use client";

import { ReactNode, useEffect } from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import {
  LayoutDashboard, CalendarClock, FileText, Pill, FlaskConical,
  Users, Building2, Bell, LogOut, HeartPulse, Stethoscope, Siren, Settings, UserCog,
} from "lucide-react";
import { useAuth, Role, ROLE_DASHBOARD_PATH } from "@/context/AuthContext";
import ThemeToggle from "./ThemeToggle";
import EkgLine from "./EkgLine";


interface NavItem {
  label: string;
  href: string;
  icon: React.ElementType;
}

const NAV_BY_ROLE: Record<Role, NavItem[]> = {
  patient: [
    { label: "Dashboard", href: "/dashboard/patient", icon: LayoutDashboard },
    { label: "Appointments", href: "/dashboard/patient/appointments", icon: CalendarClock },
    { label: "Medical Records", href: "/dashboard/patient/records", icon: FileText },
    { label: "Prescription Reader", href: "/dashboard/patient/prescription-reader", icon: FileText },
    { label: "AI Assistant", href: "/dashboard/patient/ai-assistant", icon: HeartPulse },
    { label: "Emergency SOS", href: "/dashboard/patient/sos", icon: Siren },
    { label: "Lab Tests", href: "/dashboard/patient/lab-tests", icon: FlaskConical },
  ],
  doctor: [
    { label: "Dashboard", href: "/dashboard/doctor", icon: LayoutDashboard },
    { label: "Appointments", href: "/dashboard/doctor/appointments", icon: CalendarClock },
    { label: "My Patients", href: "/dashboard/doctor/patients", icon: Users },
    { label: "Prescriptions", href: "/dashboard/doctor/prescriptions", icon: Stethoscope },
    { label: "Prescription Reviews", href: "/dashboard/doctor/prescription-reader", icon: FileText },
    { label: "My Profile", href: "/dashboard/doctor/profile", icon: UserCog },
  ],
  hospital_admin: [
    { label: "Dashboard", href: "/dashboard/hospital-admin", icon: LayoutDashboard },
    { label: "Doctors", href: "/dashboard/hospital-admin/doctors", icon: Stethoscope },
    { label: "Patients", href: "/dashboard/hospital-admin/patients", icon: Users },
    { label: "Departments", href: "/dashboard/hospital-admin/departments", icon: Building2 },
  ],
  laboratory: [
    { label: "Dashboard", href: "/dashboard/laboratory", icon: LayoutDashboard },
    { label: "Test Requests", href: "/dashboard/laboratory/requests", icon: FlaskConical },
  ],
  pharmacy: [
    { label: "Dashboard", href: "/dashboard/pharmacy", icon: LayoutDashboard },
    { label: "Inventory", href: "/dashboard/pharmacy/inventory", icon: Pill },
    { label: "Orders", href: "/dashboard/pharmacy/orders", icon: FileText },
    { label: "Prescriptions", href: "/dashboard/pharmacy/prescriptions", icon: Stethoscope },
  ],
};

export default function DashboardShell({ children }: { children: ReactNode }) {
  const { user, isLoading, logout } = useAuth();
  const pathname = usePathname();
  const router = useRouter();

  useEffect(() => {
    if (!isLoading && !user) {
      router.replace("/login");
    }
    if (user) {
      const rolePaths = Object.values(ROLE_DASHBOARD_PATH);
      if (rolePaths.some((path) => pathname.startsWith(path)) && !pathname.startsWith(ROLE_DASHBOARD_PATH[user.role])) {
        router.replace(ROLE_DASHBOARD_PATH[user.role]);
      }
    }
  }, [isLoading, user, router, pathname]);

  if (isLoading || !user || (Object.values(ROLE_DASHBOARD_PATH).some((path) => pathname.startsWith(path)) && !pathname.startsWith(ROLE_DASHBOARD_PATH[user.role]))) {
    return (
      <div className="flex h-screen items-center justify-center">
        <EkgLine width={200} height={40} />
      </div>
    );
  }

  const navItems = NAV_BY_ROLE[user.role] || [];
  const allNavItems = [...navItems, { label: "Settings", href: "/dashboard/settings", icon: Settings }];

  return (
    <div className="flex min-h-screen">
      <aside className="glass sticky top-0 hidden h-screen w-64 shrink-0 flex-col justify-between rounded-none border-r p-6 md:flex">
        <div>
          <Link href="/" className="mb-10 flex items-center gap-2 font-display text-lg font-bold text-[var(--color-primary)]">
            <HeartPulse className="text-[var(--color-accent)]" size={22} />
            AIHMS
          </Link>
          <nav className="space-y-1">
            {allNavItems.map((item) => {
              const Icon = item.icon;
              const active = pathname === item.href;
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={`flex items-center gap-3 rounded-xl px-4 py-2.5 text-sm font-medium transition-colors ${
                    active
                      ? "bg-[var(--color-primary)] text-white"
                      : "text-[var(--color-text-muted)] hover:bg-black/5 dark:hover:bg-white/5"
                  }`}
                >
                  <Icon size={17} />
                  {item.label}
                </Link>
              );
            })}
          </nav>
        </div>
        <button
          onClick={logout}
          className="flex items-center gap-3 rounded-xl px-4 py-2.5 text-sm font-medium text-[var(--color-alert)] hover:bg-red-500/10"
        >
          <LogOut size={17} /> Logout
        </button>
      </aside>

      <div className="flex min-h-screen flex-1 flex-col">
        <header className="glass sticky top-0 z-10 flex items-center justify-between rounded-none border-b px-6 py-4">
          <div>
            <p className="text-xs uppercase tracking-wide text-[var(--color-text-muted)]">
              {user.role.replace("_", " ")}
            </p>
            <h1 className="font-display text-lg font-semibold">
              Welcome, {user.first_name || user.username}
            </h1>
          </div>
          <div className="flex items-center gap-3">

            <ThemeToggle />
          </div>
        </header>
        <details className="border-b border-black/10 p-4 md:hidden dark:border-white/10">
          <summary className="cursor-pointer font-semibold">Navigation</summary>
          <nav className="mt-3 grid grid-cols-2 gap-2">{allNavItems.map((item) => <Link key={item.href} href={item.href} className="rounded-lg p-2 text-sm">{item.label}</Link>)}<button onClick={logout} className="p-2 text-left text-sm text-red-600">Log out</button></nav>
        </details>
        <main className="min-w-0 flex-1 p-4 md:p-6">{children}</main>
      </div>
    </div>
  );
}
