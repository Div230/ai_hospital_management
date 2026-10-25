"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Video } from "lucide-react";
import api from "@/lib/api";
import DashboardShell from "@/components/DashboardShell";
import GlassCard from "@/components/GlassCard";
import Badge from "@/components/Badge";

interface Appointment {
  id: string;
  patient_name: string;
  scheduled_date: string;
  scheduled_time: string;
  mode: string;
  status: string;
  reason: string;
}

const statusTone: Record<string, "vital" | "warn" | "alert" | "neutral"> = {
  CONFIRMED: "vital", PENDING: "warn", CANCELLED: "alert", COMPLETED: "neutral",
};

export default function DoctorAppointmentsPage() {
  const [appointments, setAppointments] = useState<Appointment[]>([]);
  const [filter, setFilter] = useState("");

  function load() {
    api.get("/appointments/my/", { params: filter ? { status: filter } : {} })
      .then((r) => setAppointments(r.data.results ?? r.data)).catch(() => {});
  }

  useEffect(() => { load(); }, [filter]);

  return (
    <DashboardShell>
      <div className="mb-6 flex items-center justify-between">
        <h1 className="font-display text-xl font-bold">Appointments</h1>
        <select value={filter} onChange={(e) => setFilter(e.target.value)}
          className="rounded-xl border border-black/10 bg-white/40 px-4 py-2 text-sm outline-none dark:border-white/10 dark:bg-white/5">
          <option value="">All</option>
          <option value="PENDING">Pending</option>
          <option value="CONFIRMED">Confirmed</option>
          <option value="COMPLETED">Completed</option>
          <option value="CANCELLED">Cancelled</option>
        </select>
      </div>

      <div className="space-y-3">
        {appointments.length ? appointments.map((a) => (
          <GlassCard key={a.id} className="flex flex-wrap items-center justify-between gap-4">
            <div>
              <p className="font-medium">{a.patient_name}</p>
              <p className="text-xs text-[var(--color-text-muted)]">
                {a.scheduled_date} at {a.scheduled_time} · {a.mode.replace("_", " ")}
              </p>
              {a.reason && <p className="mt-1 text-xs text-[var(--color-text-muted)]">&ldquo;{a.reason}&rdquo;</p>}
            </div>
            <div className="flex items-center gap-2">
              <Badge tone={statusTone[a.status] ?? "neutral"}>{a.status}</Badge>
              {a.mode === "VIDEO" && a.status === "CONFIRMED" && (
                <Link href={`/dashboard/video-call/${a.id}`}>
                  <button className="flex items-center gap-1 rounded-lg bg-[var(--color-accent)] px-3 py-1.5 text-xs font-semibold text-white">
                    <Video size={13} /> Join
                  </button>
                </Link>
              )}
            </div>
          </GlassCard>
        )) : (
          <GlassCard className="text-center text-sm text-[var(--color-text-muted)]">No appointments found.</GlassCard>
        )}
      </div>
    </DashboardShell>
  );
}
