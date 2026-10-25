"use client";

import { useEffect, useState } from "react";
import { UserCog, Video } from "lucide-react";
import api, { getApiErrorMessage } from "@/lib/api";
import DashboardShell from "@/components/DashboardShell";
import GlassCard from "@/components/GlassCard";
import Button from "@/components/Button";

interface DoctorProfile {
  specialization: string;
  qualification: string;
  registration_number: string;
  years_of_experience: number;
  consultation_fee: string;
  bio: string;
  is_available_for_video: boolean;
}

export default function DoctorProfilePage() {
  const [form, setForm] = useState<DoctorProfile>({
    specialization: "",
    qualification: "",
    registration_number: "",
    years_of_experience: 0,
    consultation_fee: "",
    bio: "",
    is_available_for_video: false,
  });
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  useEffect(() => {
    api.get("/doctors/me/").then((r) => {
      const d = r.data;
      setForm({
        specialization: d.specialization || "",
        qualification: d.qualification || "",
        registration_number: d.registration_number || "",
        years_of_experience: d.years_of_experience || 0,
        consultation_fee: d.consultation_fee || "",
        bio: d.bio || "",
        is_available_for_video: d.is_available_for_video || false,
      });
    }).catch(() => {});
  }, []);

  function update<K extends keyof DoctorProfile>(key: K, value: DoctorProfile[K]) {
    setForm((f) => ({ ...f, [key]: value }));
  }

  async function handleSave(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError("");
    setMessage("");
    try {
      await api.patch("/doctors/me/", form);
      setMessage("Profile updated successfully!");
    } catch (err) {
      setError(getApiErrorMessage(err));
    } finally {
      setLoading(false);
    }
  }

  return (
    <DashboardShell>
      <h1 className="mb-6 font-display text-xl font-bold">My Profile</h1>

      <GlassCard hover={false} className="max-w-2xl">
        <div className="mb-4 flex items-center gap-2">
          <UserCog size={18} className="text-[var(--color-primary)]" />
          <h2 className="font-display font-semibold">Professional details</h2>
        </div>

        {error && <p className="mb-3 text-sm text-red-600">{error}</p>}
        {message && <p className="mb-3 text-sm text-[var(--color-vital)]">{message}</p>}

        <form onSubmit={handleSave} className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="mb-1.5 block text-sm font-medium">Specialization</label>
              <input value={form.specialization} onChange={(e) => update("specialization", e.target.value)}
                className="w-full rounded-xl border border-black/10 bg-white/40 px-4 py-2.5 text-sm outline-none dark:border-white/10 dark:bg-white/5" />
            </div>
            <div>
              <label className="mb-1.5 block text-sm font-medium">Qualification</label>
              <input value={form.qualification} onChange={(e) => update("qualification", e.target.value)}
                className="w-full rounded-xl border border-black/10 bg-white/40 px-4 py-2.5 text-sm outline-none dark:border-white/10 dark:bg-white/5" />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="mb-1.5 block text-sm font-medium">Registration number</label>
              <input value={form.registration_number} onChange={(e) => update("registration_number", e.target.value)}
                className="w-full rounded-xl border border-black/10 bg-white/40 px-4 py-2.5 text-sm outline-none dark:border-white/10 dark:bg-white/5" />
            </div>
            <div>
              <label className="mb-1.5 block text-sm font-medium">Years of experience</label>
              <input type="number" value={form.years_of_experience}
                onChange={(e) => update("years_of_experience", Number(e.target.value))}
                className="w-full rounded-xl border border-black/10 bg-white/40 px-4 py-2.5 text-sm outline-none dark:border-white/10 dark:bg-white/5" />
            </div>
          </div>

          <div>
            <label className="mb-1.5 block text-sm font-medium">Consultation fee (₹)</label>
            <input type="number" step="0.01" value={form.consultation_fee}
              onChange={(e) => update("consultation_fee", e.target.value)}
              className="w-full rounded-xl border border-black/10 bg-white/40 px-4 py-2.5 text-sm outline-none dark:border-white/10 dark:bg-white/5" />
          </div>

          <div>
            <label className="mb-1.5 block text-sm font-medium">Bio</label>
            <textarea rows={4} value={form.bio} onChange={(e) => update("bio", e.target.value)}
              className="w-full rounded-xl border border-black/10 bg-white/40 px-4 py-2.5 text-sm outline-none dark:border-white/10 dark:bg-white/5" />
          </div>

          <label className="flex items-center gap-2 text-sm">
            <input type="checkbox" checked={form.is_available_for_video}
              onChange={(e) => update("is_available_for_video", e.target.checked)} />
            <Video size={15} /> Available for video consultations
          </label>

          <Button type="submit" loading={loading} className="w-full">Save changes</Button>
        </form>
      </GlassCard>
    </DashboardShell>
  );
}
