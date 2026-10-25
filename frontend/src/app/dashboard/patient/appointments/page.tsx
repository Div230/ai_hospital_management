"use client";

import { useEffect, useState } from "react";
import { CalendarClock, Search, X, RefreshCw, Video } from "lucide-react";
import Link from "next/link";
import api, { getApiErrorMessage } from "@/lib/api";
import DashboardShell from "@/components/DashboardShell";
import GlassCard from "@/components/GlassCard";
import Badge from "@/components/Badge";
import Button from "@/components/Button";

interface Doctor {
  id: string;
  full_name: string;
  specialization: string;
  consultation_fee: string;
  years_of_experience: number;
  is_available_for_video: boolean;
  rating: string;
}

interface Appointment {
  id: string;
  doctor_name: string;
  scheduled_date: string;
  scheduled_time: string;
  mode: string;
  status: string;
  reason: string;
}

const statusTone: Record<string, "vital" | "warn" | "alert" | "neutral"> = {
  CONFIRMED: "vital",
  PENDING: "warn",
  CANCELLED: "alert",
  COMPLETED: "neutral",
  RESCHEDULED: "warn",
};

export default function PatientAppointmentsPage() {
  const [appointments, setAppointments] = useState<Appointment[]>([]);
  const [doctors, setDoctors] = useState<Doctor[]>([]);
  const [search, setSearch] = useState("");
  const [showBooking, setShowBooking] = useState(false);
  const [selectedDoctor, setSelectedDoctor] = useState<Doctor | null>(null);
  const [bookingForm, setBookingForm] = useState({ scheduled_date: "", scheduled_time: "", mode: "IN_PERSON", reason: "" });
  const [slots, setSlots] = useState<string[]>([]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  function loadAppointments() {
    api.get("/appointments/my/").then((r) => setAppointments(r.data.results ?? r.data)).catch(() => {});
  }

  useEffect(() => {
    loadAppointments();
  }, []);

  function searchDoctors() {
    api.get("/doctors/directory/", { params: { search } }).then((r) => setDoctors(r.data.results ?? r.data)).catch(() => {});
  }

  useEffect(() => {
    if (showBooking) searchDoctors();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [showBooking]);

  useEffect(() => {
    setSlots([]);
    if (!selectedDoctor || !bookingForm.scheduled_date) return;
    let active = true;
    api.get(`/doctors/${selectedDoctor.id}/slots/`, { params: { date: bookingForm.scheduled_date } })
      .then(({ data }: { data: { slots: string[] } }) => { if (active) setSlots(data.slots); })
      .catch((err: unknown) => { if (active) setError(getApiErrorMessage(err)); });
    return () => { active = false; };
  }, [selectedDoctor?.id, bookingForm.scheduled_date]);

  async function handleBook(e: React.FormEvent) {
    e.preventDefault();
    if (!selectedDoctor) return;
    setLoading(true);
    setError("");
    try {
      await api.post("/appointments/book/", {
        doctor_id: selectedDoctor.id,
        ...bookingForm,
      });
      setShowBooking(false);
      setSelectedDoctor(null);
      setBookingForm({ scheduled_date: "", scheduled_time: "", mode: "IN_PERSON", reason: "" });
      loadAppointments();
    } catch (err) {
      setError(getApiErrorMessage(err));
    } finally {
      setLoading(false);
    }
  }

  async function handleCancel(id: string) {
    try {
      await api.post(`/appointments/${id}/cancel/`, { reason: "Cancelled by patient" });
      loadAppointments();
    } catch (err) { setError(getApiErrorMessage(err)); }
  }

  return (
    <DashboardShell>
      <div className="mb-6 flex items-center justify-between">
        <h1 className="font-display text-xl font-bold">Appointments</h1>
        <Button onClick={() => setShowBooking(true)}>
          <CalendarClock size={16} /> Book new
        </Button>
      </div>

      {error && !showBooking && <p role="alert" className="mb-4 text-red-600">{error}</p>}
      {showBooking && (
        <GlassCard hover={false} className="mb-6">
          <div className="mb-4 flex items-center justify-between">
            <h2 className="font-display font-semibold">Book an appointment</h2>
            <button onClick={() => { setShowBooking(false); setSelectedDoctor(null); }}>
              <X size={18} />
            </button>
          </div>

          {!selectedDoctor ? (
            <>
              <div className="relative mb-4">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-[var(--color-text-muted)]" size={16} />
                <input
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  onKeyUp={(e) => e.key === "Enter" && searchDoctors()}
                  placeholder="Search by specialization or name..."
                  className="w-full rounded-xl border border-black/10 bg-white/40 py-2.5 pl-10 pr-4 text-sm outline-none focus:border-[var(--color-primary)] dark:border-white/10 dark:bg-white/5"
                />
              </div>
              <div className="grid gap-3 sm:grid-cols-2">
                {doctors.map((d) => (
                  <button
                    key={d.id}
                    onClick={() => setSelectedDoctor(d)}
                    className="glass-hover glass rounded-xl p-4 text-left"
                  >
                    <p className="font-medium">Dr. {d.full_name}</p>
                    <p className="text-xs text-[var(--color-text-muted)]">{d.specialization} · {d.years_of_experience} yrs exp</p>
                    <p className="mt-1 text-xs font-data">₹{d.consultation_fee}</p>
                  </button>
                ))}
                {!doctors.length && <p className="text-sm text-[var(--color-text-muted)]">No doctors found. Try a different search.</p>}
              </div>
            </>
          ) : (
            <form onSubmit={handleBook} className="space-y-4">
              <div className="rounded-xl bg-black/[0.03] p-3 text-sm dark:bg-white/[0.05]">
                Booking with <strong>Dr. {selectedDoctor.full_name}</strong> ({selectedDoctor.specialization})
                <button type="button" onClick={() => setSelectedDoctor(null)} className="ml-2 text-xs text-[var(--color-primary)] underline">change</button>
              </div>
              {error && <p className="text-sm text-red-600">{error}</p>}
              <div className="grid grid-cols-2 gap-4">
                <input required type="date" value={bookingForm.scheduled_date}
                  onChange={(e) => setBookingForm((f) => ({ ...f, scheduled_date: e.target.value, scheduled_time: "" }))}
                  className="rounded-xl border border-black/10 bg-white/40 px-4 py-2.5 text-sm outline-none dark:border-white/10 dark:bg-white/5" />
                <select required aria-label="Available time slot" value={bookingForm.scheduled_time}
                  onChange={(e) => setBookingForm((f) => ({ ...f, scheduled_time: e.target.value }))}
                  className="rounded-xl border border-black/10 bg-white/40 px-4 py-2.5 text-sm outline-none dark:border-white/10 dark:bg-white/5">
                  <option value="">{slots.length ? "Select available time (IST)" : "No available slots"}</option>
                  {slots.map((slot) => <option key={slot} value={slot}>{slot.slice(0, 5)}</option>)}
                </select>
              </div>
              <select value={bookingForm.mode} onChange={(e) => setBookingForm((f) => ({ ...f, mode: e.target.value }))}
                className="w-full rounded-xl border border-black/10 bg-white/40 px-4 py-2.5 text-sm outline-none dark:border-white/10 dark:bg-white/5">
                <option value="IN_PERSON">In Person</option>
                <option value="VIDEO">Video Consultation</option>
              </select>
              <textarea placeholder="Reason for visit (optional)" value={bookingForm.reason}
                onChange={(e) => setBookingForm((f) => ({ ...f, reason: e.target.value }))}
                className="w-full rounded-xl border border-black/10 bg-white/40 px-4 py-2.5 text-sm outline-none dark:border-white/10 dark:bg-white/5" rows={3} />
              <Button type="submit" loading={loading} className="w-full">Confirm booking</Button>
            </form>
          )}
        </GlassCard>
      )}

      <div className="space-y-3">
        {appointments.length ? (
          appointments.map((a) => (
            <GlassCard key={a.id} className="flex flex-wrap items-center justify-between gap-4">
              <div>
                <p className="font-medium">Dr. {a.doctor_name}</p>
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
                {["PENDING", "CONFIRMED"].includes(a.status) && (
                  <button onClick={() => handleCancel(a.id)} className="rounded-lg p-2 text-[var(--color-alert)] hover:bg-red-500/10">
                    <X size={16} />
                  </button>
                )}
              </div>
            </GlassCard>
          ))
        ) : (
          <GlassCard className="text-center text-sm text-[var(--color-text-muted)]">
            No appointments yet. Book your first one above.
          </GlassCard>
        )}
      </div>
    </DashboardShell>
  );
}
