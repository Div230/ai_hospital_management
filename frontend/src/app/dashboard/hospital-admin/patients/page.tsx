"use client";

import { useEffect, useState } from "react";
import api from "@/lib/api";
import DashboardShell from "@/components/DashboardShell";
import GlassCard from "@/components/GlassCard";

interface Patient {
  id: string;
  full_name: string;
  email: string;
  blood_group: string;
}

export default function ManagedPatientsPage() {
  const [patients, setPatients] = useState<Patient[]>([]);
  useEffect(() => {
    api.get("/hospital-admin/patients/").then((r) => setPatients(r.data.results ?? r.data)).catch(() => {});
  }, []);

  return (
    <DashboardShell>
      <h1 className="mb-6 font-display text-xl font-bold">Patients</h1>
      <GlassCard>
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-black/10 text-left text-xs text-[var(--color-text-muted)] dark:border-white/10">
              <th className="pb-2">Name</th><th className="pb-2">Email</th><th className="pb-2">Blood Group</th>
            </tr>
          </thead>
          <tbody>
            {patients.map((p) => (
              <tr key={p.id} className="border-b border-black/5 last:border-0 dark:border-white/5">
                <td className="py-2.5">{p.full_name}</td>
                <td className="py-2.5 text-[var(--color-text-muted)]">{p.email}</td>
                <td className="py-2.5">{p.blood_group || "—"}</td>
              </tr>
            ))}
          </tbody>
        </table>
        {!patients.length && <p className="py-6 text-center text-sm text-[var(--color-text-muted)]">No patients served yet.</p>}
      </GlassCard>
    </DashboardShell>
  );
}
