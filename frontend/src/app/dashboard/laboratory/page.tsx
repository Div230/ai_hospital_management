"use client";

import { useEffect, useState } from "react";
import { FlaskConical, Clock3, CheckCircle2 } from "lucide-react";
import api from "@/lib/api";
import DashboardShell from "@/components/DashboardShell";
import GlassCard from "@/components/GlassCard";

interface LabStats {
  pending_requests: number;
  in_progress: number;
  completed_today: number;
}

export default function LabDashboardPage() {
  const [stats, setStats] = useState<LabStats | null>(null);
  useEffect(() => {
    api.get("/core/dashboard/lab/").then((r) => setStats(r.data)).catch(() => {});
  }, []);

  return (
    <DashboardShell>
      <div className="grid gap-6 md:grid-cols-3">
        <StatCard icon={FlaskConical} label="Pending Requests" value={stats?.pending_requests ?? 0} />
        <StatCard icon={Clock3} label="In Progress" value={stats?.in_progress ?? 0} />
        <StatCard icon={CheckCircle2} label="Completed Today" value={stats?.completed_today ?? 0} />
      </div>
      <GlassCard className="mt-6">
        <h2 className="font-display font-semibold">Test requests</h2>
        <p className="mt-2 text-sm text-[var(--color-text-muted)]">
          Manage incoming blood/X-ray/MRI/CT test requests, upload digital reports, and patients
          get auto-notified the moment AI analysis (OCR + abnormal-value detection) completes.
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
