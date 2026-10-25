"use client";

import { useEffect, useState } from "react";
import { User } from "lucide-react";
import api from "@/lib/api";
import DashboardShell from "@/components/DashboardShell";
import GlassCard from "@/components/GlassCard";
import Badge from "@/components/Badge";

interface Patient {
  id: string;
  full_name: string;
  email: string;
  blood_group: string;
  gender: string;
  ai_health_score: number | null;
}

export default function DoctorPatientsPage() {
  const [patients, setPatients] = useState<Patient[]>([]);

  useEffect(() => {
    api.get("/doctors/my-patients/").then((r) => setPatients(r.data.results ?? r.data)).catch(() => {});
  }, []);

  return (
    <DashboardShell>
      <h1 className="mb-6 font-display text-xl font-bold">My Patients</h1>
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {patients.length ? patients.map((p) => (
          <GlassCard key={p.id}>
            <div className="mb-3 flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-full bg-[var(--color-primary)]/10 text-[var(--color-primary)]">
                <User size={18} />
              </div>
              <div>
                <p className="font-medium">{p.full_name}</p>
                <p className="text-xs text-[var(--color-text-muted)]">{p.email}</p>
              </div>
            </div>
            <div className="flex flex-wrap gap-2">
              {p.blood_group && <Badge tone="neutral">{p.blood_group}</Badge>}
              {p.ai_health_score != null && <Badge tone="accent">Health Score: {p.ai_health_score}</Badge>}
            </div>
          </GlassCard>
        )) : (
          <GlassCard className="text-center text-sm text-[var(--color-text-muted)] md:col-span-3">
            No patients yet — they&apos;ll show up here once they book an appointment with you.
          </GlassCard>
        )}
      </div>
    </DashboardShell>
  );
}
