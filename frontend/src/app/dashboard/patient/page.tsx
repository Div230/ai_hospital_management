"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { CalendarClock, Pill, Syringe, Bell, ActivitySquare, Siren, ArrowRight } from "lucide-react";
import api from "@/lib/api";
import DashboardShell from "@/components/DashboardShell";
import GlassCard from "@/components/GlassCard";
import Badge from "@/components/Badge";
import EkgLine from "@/components/EkgLine";

interface DashboardData {
  ai_health_score: number | null;
  ai_risk_flags: string[];
  upcoming_appointments: { id: string; doctor: string; date: string; time: string; mode: string }[];
  active_medicine_reminders: number;
  pending_vaccinations: number;
  unread_notifications: number;
}

export default function PatientDashboardPage() {
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api
      .get("/core/dashboard/patient/")
      .then((res) => setData(res.data))
      .catch(() => setData(null))
      .finally(() => setLoading(false));
  }, []);

  return (
    <DashboardShell>
      <div className="grid gap-6 lg:grid-cols-3">
        <GlassCard className="lg:col-span-2" hover={false}>
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs text-[var(--color-text-muted)]">AI Health Score</p>
              <p className="font-data text-4xl font-bold text-[var(--color-vital)]">
                {loading ? "—" : data?.ai_health_score ?? "N/A"}
              </p>
            </div>
            <Badge tone="accent">{data?.ai_health_score == null ? "Not assessed" : "Unverified estimate"}</Badge>
          </div>
          <EkgLine width={500} height={70} className="mt-4 w-full" />
          {!!data?.ai_risk_flags?.length && (
            <div className="mt-4 flex flex-wrap gap-2">
              {data.ai_risk_flags.map((flag) => (
                <Badge key={flag} tone="warn">{flag}</Badge>
              ))}
            </div>
          )}
        </GlassCard>

        <Link href="/dashboard/patient/sos">
          <GlassCard className="flex h-full flex-col items-center justify-center gap-3 border-red-400/30 bg-red-500/5 text-center">
            <Siren className="text-[var(--color-alert)]" size={32} />
            <p className="font-display font-bold text-[var(--color-alert)]">Emergency SOS</p>
            <p className="text-xs text-[var(--color-text-muted)]">Dispatch integration unavailable — call emergency services</p>
          </GlassCard>
        </Link>
      </div>

      <Link href="/dashboard/patient/prescription-reader" className="mt-6 block"><GlassCard className="border-teal-400/30"><p className="font-semibold">AI Prescription Reader →</p><p className="mt-1 text-sm text-[var(--color-text-muted)]">Upload an image or PDF, read the transcription, and check uncertain text.</p></GlassCard></Link>
      <div className="mt-6 grid gap-6 md:grid-cols-2 lg:grid-cols-4">
        <StatCard icon={CalendarClock} label="Upcoming" value={data?.upcoming_appointments.length ?? 0} />
        <StatCard icon={Pill} label="Active Reminders" value={data?.active_medicine_reminders ?? 0} />
        <StatCard icon={Syringe} label="Pending Vaccines" value={data?.pending_vaccinations ?? 0} />
        <StatCard icon={Bell} label="Unread Alerts" value={data?.unread_notifications ?? 0} />
      </div>

      <div className="mt-6 grid gap-6 lg:grid-cols-2">
        <GlassCard>
          <div className="mb-4 flex items-center justify-between">
            <h2 className="font-display font-semibold">Upcoming appointments</h2>
            <Link href="/dashboard/patient/appointments" className="flex items-center gap-1 text-xs text-[var(--color-primary)]">
              View all <ArrowRight size={12} />
            </Link>
          </div>
          <div className="space-y-3">
            {data?.upcoming_appointments.length ? (
              data.upcoming_appointments.map((a) => (
                <div key={a.id} className="flex items-center justify-between rounded-xl bg-black/[0.02] p-3 dark:bg-white/[0.03]">
                  <div>
                    <p className="text-sm font-medium">Dr. {a.doctor}</p>
                    <p className="text-xs text-[var(--color-text-muted)]">{a.date} at {a.time}</p>
                  </div>
                  <Badge tone={a.mode === "VIDEO" ? "accent" : "neutral"}>{a.mode.replace("_", " ")}</Badge>
                </div>
              ))
            ) : (
              <EmptyState text="No upcoming appointments yet." cta="Book one" href="/dashboard/patient/appointments" />
            )}
          </div>
        </GlassCard>

        <GlassCard>
          <div className="mb-4 flex items-center justify-between">
            <h2 className="font-display font-semibold">AI Health Assistant</h2>
            <ActivitySquare className="text-[var(--color-accent)]" size={18} />
          </div>
          <p className="text-sm text-[var(--color-text-muted)]">
            Describe your symptoms and get a triage-level assessment with follow-up questions,
            powered by our LangGraph-based symptom checker.
          </p>
          <Link href="/dashboard/patient/ai-assistant">
            <button className="mt-4 w-full rounded-xl bg-[var(--color-primary)] py-2.5 text-sm font-semibold text-white hover:bg-[var(--color-primary-dark)]">
              Start symptom check
            </button>
          </Link>
        </GlassCard>
      </div>
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

function EmptyState({ text, cta, href }: { text: string; cta: string; href: string }) {
  return (
    <div className="rounded-xl border border-dashed border-black/10 p-6 text-center dark:border-white/10">
      <p className="text-sm text-[var(--color-text-muted)]">{text}</p>
      <Link href={href} className="mt-2 inline-block text-sm font-medium text-[var(--color-primary)] hover:underline">
        {cta} →
      </Link>
    </div>
  );
}
