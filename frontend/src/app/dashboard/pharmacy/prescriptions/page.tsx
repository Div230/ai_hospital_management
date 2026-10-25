"use client";

import { useEffect, useState } from "react";
import { Stethoscope } from "lucide-react";
import api, { getApiErrorMessage } from "@/lib/api";
import DashboardShell from "@/components/DashboardShell";
import GlassCard from "@/components/GlassCard";
import Button from "@/components/Button";

interface PrescriptionItem {
  medicine_name: string;
  dosage: string;
  frequency: string;
}

interface Prescription {
  id: string;
  diagnosis: string;
  items: PrescriptionItem[];
}

export default function PharmacyPrescriptionsPage() {
  const [prescriptions, setPrescriptions] = useState<Prescription[]>([]);
  const [receivingId, setReceivingId] = useState<string | null>(null);
  const [error, setError] = useState("");

  function load() {
    api.get("/pharmacy/prescriptions/pending/").then((r) => setPrescriptions(r.data.results ?? r.data)).catch(() => {});
  }
  useEffect(() => { load(); }, []);

  async function handleReceive(id: string) {
    setReceivingId(id);
    setError("");
    try {
      await api.post(`/pharmacy/prescriptions/${id}/receive/`);
      load();
    } catch (err) {
      setError(getApiErrorMessage(err));
    } finally {
      setReceivingId(null);
    }
  }

  return (
    <DashboardShell>
      <p className="mb-6 rounded-xl bg-amber-500/10 p-4 text-sm">Only prescriptions already assigned to your pharmacy are shown. Patient-directed sharing of new prescriptions is unavailable in this version.</p>
      <h1 className="mb-6 font-display text-xl font-bold">Pending Prescriptions</h1>
      {error && <p className="mb-4 text-sm text-red-600">{error}</p>}
      <div className="space-y-4">
        {prescriptions.length ? prescriptions.map((p) => (
          <GlassCard key={p.id}>
            <div className="mb-3 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Stethoscope size={18} className="text-[var(--color-primary)]" />
                <p className="font-medium">{p.diagnosis || "Prescription"}</p>
              </div>
              <Button onClick={() => handleReceive(p.id)} loading={receivingId === p.id} className="!px-4 !py-1.5 text-xs">
                Receive & Create Order
              </Button>
            </div>
            <div className="space-y-1.5">
              {p.items?.map((it, i) => (
                <p key={i} className="text-xs text-[var(--color-text-muted)]">
                  • {it.medicine_name} — {it.dosage}, {it.frequency}
                </p>
              ))}
            </div>
          </GlassCard>
        )) : (
          <GlassCard className="text-center text-sm text-[var(--color-text-muted)]">
            No pending prescriptions right now.
          </GlassCard>
        )}
      </div>
    </DashboardShell>
  );
}
