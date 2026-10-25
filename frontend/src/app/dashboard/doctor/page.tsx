"use client";

import { useEffect, useState } from "react";
import { CalendarClock, Users, Star, Clock3 } from "lucide-react";
import api from "@/lib/api";
import DashboardShell from "@/components/DashboardShell";
import GlassCard from "@/components/GlassCard";
import Badge from "@/components/Badge";

interface DoctorDashboardData {
  todays_appointments: number;
  pending_appointments: number;
  total_patients: number;
  rating: string;
  schedule_today: { id: string; patient: string; time: string; mode: string; status: string }[];
}

const statusTone: Record<string, "vital" | "warn" | "alert" | "neutral"> = {
  CONFIRMED: "vital",
  PENDING: "warn",
  CANCELLED: "alert",
  COMPLETED: "neutral",
};

export default function DoctorDashboardPage() {
  const [data, setData] = useState<DoctorDashboardData | null>(null);

  useEffect(() => {
    api.get("/core/dashboard/doctor/").then((res) => setData(res.data)).catch(() => setData(null));
  }, []);

  return (
    <DashboardShell>
      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
        <StatCard icon={CalendarClock} label="Today's Appointments" value={data?.todays_appointments ?? 0} />
        <StatCard icon={Clock3} label="Pending" value={data?.pending_appointments ?? 0} />
        <StatCard icon={Users} label="Total Patients" value={data?.total_patients ?? 0} />
        <StatCard icon={Star} label="Rating" value={data?.rating ?? "0.00"} />
      </div>

      <GlassCard className="mt-6">
        <h2 className="mb-4 font-display font-semibold">Today&apos;s schedule</h2>
        <div className="space-y-3">
          {data?.schedule_today.length ? (
            data.schedule_today.map((appt) => (
              <div key={appt.id} className="flex items-center justify-between rounded-xl bg-black/[0.02] p-4 dark:bg-white/[0.03]">
                <div>
                  <p className="text-sm font-medium">{appt.patient}</p>
                  <p className="text-xs text-[var(--color-text-muted)]">{appt.time} · {appt.mode.replace("_", " ")}</p>
                </div>
                <Badge tone={statusTone[appt.status] ?? "neutral"}>{appt.status}</Badge>
              </div>
            ))
          ) : (
            <p className="rounded-xl border border-dashed border-black/10 p-6 text-center text-sm text-[var(--color-text-muted)] dark:border-white/10">
              No appointments scheduled for today.
            </p>
          )}
        </div>
      </GlassCard>
    </DashboardShell>
  );
}

function StatCard({ icon: Icon, label, value }: { icon: React.ElementType; label: string; value: number | string }) {
  return (
    <GlassCard className="flex items-center gap-4">
      <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-[var(--color-primary)]/10 text-[var(--color-primary)]">
        <Icon size={20} />
      </div>
      <div>
        <p className="font-data text-2xl font-bold">{value}</p>
        <p className="text-xs text-[var(--color-text-muted)]">{label}</p>
      </div>
    </GlassCard>
  );
}
