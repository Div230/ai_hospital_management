"use client";

import { useEffect, useState } from "react";
import { Plus, Trash2, Stethoscope } from "lucide-react";
import api, { getApiErrorMessage } from "@/lib/api";
import DashboardShell from "@/components/DashboardShell";
import GlassCard from "@/components/GlassCard";
import Button from "@/components/Button";
import Badge from "@/components/Badge";

interface Appointment {
  id: string;
  patient_name: string;
  scheduled_date: string;
}

interface PrescriptionItem {
  medicine_name: string;
  dosage: string;
  frequency: string;
  duration_days: number;
  instructions: string;
}

interface Prescription {
  id: string;
  diagnosis: string;
  notes: string;
  is_sent_to_pharmacy: boolean;
  items: (PrescriptionItem & { ai_explanation?: string })[];
}

const emptyItem: PrescriptionItem = { medicine_name: "", dosage: "", frequency: "", duration_days: 5, instructions: "" };

export default function PrescriptionsPage() {
  const [appointments, setAppointments] = useState<Appointment[]>([]);
  const [prescriptions, setPrescriptions] = useState<Prescription[]>([]);
  const [appointmentId, setAppointmentId] = useState("");
  const [diagnosis, setDiagnosis] = useState("");
  const [notes, setNotes] = useState("");
  const [items, setItems] = useState<PrescriptionItem[]>([{ ...emptyItem }]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    api.get("/appointments/my/", { params: { status: "CONFIRMED" } })
      .then((r) => setAppointments(r.data.results ?? r.data)).catch(() => {});
    api.get("/appointments/prescriptions/").then((r) => setPrescriptions(r.data.results ?? r.data)).catch(() => {});
  }, []);

  function updateItem(index: number, field: keyof PrescriptionItem, value: string | number) {
    setItems((prev) => prev.map((it, i) => (i === index ? { ...it, [field]: value } : it)));
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!appointmentId) return;
    setLoading(true);
    setError("");
    try {
      const { data } = await api.post("/appointments/prescriptions/", {
        appointment: appointmentId,
        diagnosis,
        notes,
        items,
      });
      setPrescriptions((p) => [data, ...p]);
      setAppointmentId(""); setDiagnosis(""); setNotes(""); setItems([{ ...emptyItem }]);
    } catch (err) {
      setError(getApiErrorMessage(err));
    } finally {
      setLoading(false);
    }
  }

  return (
    <DashboardShell>
      <h1 className="mb-6 font-display text-xl font-bold">Prescriptions</h1>

      <div className="grid gap-6 lg:grid-cols-2">
        <GlassCard hover={false}>
          <div className="mb-4 flex items-center gap-2">
            <Stethoscope size={18} className="text-[var(--color-primary)]" />
            <h2 className="font-display font-semibold">New digital prescription</h2>
          </div>
          {error && <p className="mb-3 text-sm text-red-600">{error}</p>}
          <form onSubmit={handleSubmit} className="space-y-4">
            <select required value={appointmentId} onChange={(e) => setAppointmentId(e.target.value)}
              className="w-full rounded-xl border border-black/10 bg-white/40 px-4 py-2.5 text-sm outline-none dark:border-white/10 dark:bg-white/5">
              <option value="">Select appointment...</option>
              {appointments.map((a) => (
                <option key={a.id} value={a.id}>{a.patient_name} — {a.scheduled_date}</option>
              ))}
            </select>
            <input placeholder="Diagnosis" value={diagnosis} onChange={(e) => setDiagnosis(e.target.value)}
              className="w-full rounded-xl border border-black/10 bg-white/40 px-4 py-2.5 text-sm outline-none dark:border-white/10 dark:bg-white/5" />

            <div className="space-y-3">
              {items.map((item, i) => (
                <div key={i} className="rounded-xl bg-black/[0.02] p-3 dark:bg-white/[0.04]">
                  <div className="grid grid-cols-2 gap-2">
                    <input required placeholder="Medicine name" value={item.medicine_name}
                      onChange={(e) => updateItem(i, "medicine_name", e.target.value)}
                      className="rounded-lg border border-black/10 bg-white/60 px-3 py-2 text-xs outline-none dark:border-white/10 dark:bg-white/5" />
                    <input required placeholder="Dosage (e.g. 500mg)" value={item.dosage}
                      onChange={(e) => updateItem(i, "dosage", e.target.value)}
                      className="rounded-lg border border-black/10 bg-white/60 px-3 py-2 text-xs outline-none dark:border-white/10 dark:bg-white/5" />
                    <input required placeholder="Frequency (e.g. 2x/day)" value={item.frequency}
                      onChange={(e) => updateItem(i, "frequency", e.target.value)}
                      className="rounded-lg border border-black/10 bg-white/60 px-3 py-2 text-xs outline-none dark:border-white/10 dark:bg-white/5" />
                    <input required type="number" placeholder="Duration (days)" value={item.duration_days}
                      onChange={(e) => updateItem(i, "duration_days", Number(e.target.value))}
                      className="rounded-lg border border-black/10 bg-white/60 px-3 py-2 text-xs outline-none dark:border-white/10 dark:bg-white/5" />
                  </div>
                  {items.length > 1 && (
                    <button type="button" onClick={() => setItems((p) => p.filter((_, idx) => idx !== i))}
                      className="mt-2 flex items-center gap-1 text-xs text-[var(--color-alert)]">
                      <Trash2 size={12} /> Remove
                    </button>
                  )}
                </div>
              ))}
            </div>
            <button type="button" onClick={() => setItems((p) => [...p, { ...emptyItem }])}
              className="flex items-center gap-1 text-sm text-[var(--color-primary)]">
              <Plus size={14} /> Add medicine
            </button>

            <Button type="submit" loading={loading} className="w-full">Issue prescription</Button>
          </form>
        </GlassCard>

        <div className="space-y-4">
          {prescriptions.map((p) => (
            <GlassCard key={p.id}>
              <div className="mb-2 flex items-center justify-between">
                <p className="font-medium">{p.diagnosis || "Prescription"}</p>
                {p.is_sent_to_pharmacy && <Badge tone="vital">Sent to pharmacy</Badge>}
              </div>
              <div className="space-y-2">
                {p.items?.map((it, i) => (
                  <div key={i} className="rounded-lg bg-black/[0.02] p-2.5 text-xs dark:bg-white/[0.03]">
                    <p className="font-medium">{it.medicine_name} — {it.dosage}, {it.frequency}, {it.duration_days} days</p>
                    {it.ai_explanation && <p className="mt-1 text-[var(--color-text-muted)]">{it.ai_explanation}</p>}
                  </div>
                ))}
              </div>
            </GlassCard>
          ))}
        </div>
      </div>
    </DashboardShell>
  );
}
