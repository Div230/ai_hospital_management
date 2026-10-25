"use client";

import { useEffect, useState } from "react";
import { Stethoscope, Users, Building2, Layers, IndianRupee } from "lucide-react";
import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from "recharts";
import api from "@/lib/api";
import DashboardShell from "@/components/DashboardShell";
import GlassCard from "@/components/GlassCard";

interface Stats {
  total_doctors: number;
  total_departments: number;
  total_staff: number;
  total_patients_served: number;
  appointments_today: number;
}

interface Revenue {
  consultation_revenue: number;
  pharmacy_revenue: number;
  total_revenue: number;
  note: string;
}

interface TrendPoint {
  scheduled_date: string;
  count: number;
}

export default function HospitalAdminDashboard() {
  const [stats, setStats] = useState<Stats | null>(null);
  const [revenue, setRevenue] = useState<Revenue | null>(null);
  const [trend, setTrend] = useState<TrendPoint[]>([]);

  useEffect(() => {
    api.get("/hospital-admin/analytics/statistics/").then((r) => setStats(r.data)).catch(() => {});
    api.get("/hospital-admin/analytics/revenue/").then((r) => setRevenue(r.data)).catch(() => {});
    api.get("/hospital-admin/analytics/appointments/").then((r) => setTrend(r.data.daily_trend_last_30_days ?? [])).catch(() => {});
  }, []);

  return (
    <DashboardShell>
      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-5">
        <StatCard icon={Stethoscope} label="Doctors" value={stats?.total_doctors ?? 0} />
        <StatCard icon={Building2} label="Departments" value={stats?.total_departments ?? 0} />
        <StatCard icon={Layers} label="Staff" value={stats?.total_staff ?? 0} />
        <StatCard icon={Users} label="Patients Served" value={stats?.total_patients_served ?? 0} />
        <StatCard icon={IndianRupee} label="Today's Appointments" value={stats?.appointments_today ?? 0} />
      </div>

      <GlassCard className="mt-6">
        <h2 className="mb-4 font-display font-semibold">Appointment trend (last 30 days)</h2>
        <div className="h-64">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={trend}>
              <defs>
                <linearGradient id="trendFill" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="var(--color-primary)" stopOpacity={0.35} />
                  <stop offset="100%" stopColor="var(--color-primary)" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(148,163,184,0.15)" />
              <XAxis dataKey="scheduled_date" tick={{ fontSize: 11 }} />
              <YAxis allowDecimals={false} tick={{ fontSize: 11 }} />
              <Tooltip />
              <Area type="monotone" dataKey="count" stroke="var(--color-primary)" fill="url(#trendFill)" strokeWidth={2} />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </GlassCard>

      <GlassCard className="mt-6">
        <h2 className="mb-4 font-display font-semibold">Revenue overview (demo)</h2>
        <div className="grid gap-4 sm:grid-cols-3">
          <div>
            <p className="text-xs text-[var(--color-text-muted)]">Consultations</p>
            <p className="font-data text-2xl font-bold">₹{revenue?.consultation_revenue?.toLocaleString() ?? 0}</p>
          </div>
          <div>
            <p className="text-xs text-[var(--color-text-muted)]">Pharmacy Orders</p>
            <p className="font-data text-2xl font-bold">₹{revenue?.pharmacy_revenue?.toLocaleString() ?? 0}</p>
          </div>
          <div>
            <p className="text-xs text-[var(--color-text-muted)]">Total</p>
            <p className="font-data text-2xl font-bold text-[var(--color-vital)]">₹{revenue?.total_revenue?.toLocaleString() ?? 0}</p>
          </div>
        </div>
        {revenue?.note && <p className="mt-4 text-xs text-[var(--color-text-muted)]">{revenue.note}</p>}
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
