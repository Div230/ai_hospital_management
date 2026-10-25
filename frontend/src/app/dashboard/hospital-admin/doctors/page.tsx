"use client";

import { useEffect, useState } from "react";
import { CheckCircle2, XCircle } from "lucide-react";
import api, { getApiErrorMessage } from "@/lib/api";
import DashboardShell from "@/components/DashboardShell";
import GlassCard from "@/components/GlassCard";
import Badge from "@/components/Badge";
import Button from "@/components/Button";

interface Doctor {
  id: string;
  full_name: string;
  email: string;
  specialization: string;
  is_verified: boolean;
  consultation_fee: string;
}

export default function ManageDoctorsPage() {
  const [error, setError] = useState("");
  const [doctors, setDoctors] = useState<Doctor[]>([]);

  function load() {
    api.get("/hospital-admin/doctors/all/").then((r) => setDoctors(r.data.results ?? r.data)).catch(() => {});
  }
  useEffect(() => { load(); }, []);

  async function toggleVerify(doc: Doctor) {
    try {
      await api.patch(`/hospital-admin/doctors/${doc.id}/status/`, {
        is_verified: !doc.is_verified,
        assign_to_hospital: true,
      });
      load();
    } catch (err) { setError(getApiErrorMessage(err)); }
  }

  return (
    <DashboardShell>
      {error && <p role="alert" className="mb-4 text-red-600">{error}</p>}
      <h1 className="mb-6 font-display text-xl font-bold">Manage Doctors</h1>
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {doctors.map((d) => (
          <GlassCard key={d.id}>
            <p className="font-medium">Dr. {d.full_name}</p>
            <p className="text-xs text-[var(--color-text-muted)]">{d.specialization}</p>
            <p className="mt-1 text-xs text-[var(--color-text-muted)]">{d.email}</p>
            <div className="mt-3 flex items-center justify-between">
              <Badge tone={d.is_verified ? "vital" : "warn"}>{d.is_verified ? "Verified" : "Pending"}</Badge>
              <Button variant={d.is_verified ? "secondary" : "primary"} onClick={() => toggleVerify(d)} className="!px-3 !py-1.5 text-xs">
                {d.is_verified ? <XCircle size={14} /> : <CheckCircle2 size={14} />}
                {d.is_verified ? "Revoke" : "Verify & Assign"}
              </Button>
            </div>
          </GlassCard>
        ))}
        {!doctors.length && (
          <GlassCard className="text-center text-sm text-[var(--color-text-muted)] md:col-span-3">
            No doctors registered on the platform yet.
          </GlassCard>
        )}
      </div>
    </DashboardShell>
  );
}
