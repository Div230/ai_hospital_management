"use client";

import { useEffect, useState } from "react";
import { Pill, PackageX, ClipboardList, CalendarDays } from "lucide-react";
import api from "@/lib/api";
import DashboardShell from "@/components/DashboardShell";
import GlassCard from "@/components/GlassCard";

interface PharmacyStats {
  pending_orders: number;
  low_stock_medicines: number;
  total_medicines: number;
  orders_today: number;
}

export default function PharmacyDashboardPage() {
  const [stats, setStats] = useState<PharmacyStats | null>(null);
  useEffect(() => {
    api.get("/core/dashboard/pharmacy/").then((r) => setStats(r.data)).catch(() => {});
  }, []);

  return (
    <DashboardShell>
      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
        <StatCard icon={ClipboardList} label="Pending Orders" value={stats?.pending_orders ?? 0} />
        <StatCard icon={PackageX} label="Low Stock Items" value={stats?.low_stock_medicines ?? 0} />
        <StatCard icon={Pill} label="Total Medicines" value={stats?.total_medicines ?? 0} />
        <StatCard icon={CalendarDays} label="Orders Today" value={stats?.orders_today ?? 0} />
      </div>
      <GlassCard className="mt-6">
        <h2 className="font-display font-semibold">Digital prescriptions</h2>
        <p className="mt-2 text-sm text-[var(--color-text-muted)]">
          Receive prescriptions straight from doctors, auto-match against your inventory,
          and track orders from placed to delivered.
        </p>
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
