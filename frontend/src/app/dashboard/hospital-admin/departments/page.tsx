"use client";

import { useEffect, useState } from "react";
import { Plus, Building2 } from "lucide-react";
import api, { getApiErrorMessage } from "@/lib/api";
import DashboardShell from "@/components/DashboardShell";
import GlassCard from "@/components/GlassCard";
import Button from "@/components/Button";

interface Department {
  id: string;
  name: string;
  description: string;
  doctor_count: number;
}

export default function DepartmentsPage() {
  const [departments, setDepartments] = useState<Department[]>([]);
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  function load() {
    api.get("/hospital-admin/departments/").then((r) => setDepartments(r.data.results ?? r.data)).catch(() => {});
  }
  useEffect(() => { load(); }, []);

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError("");
    try {
      await api.post("/hospital-admin/departments/", { name, description });
      setName(""); setDescription("");
      load();
    } catch (err) {
      setError(getApiErrorMessage(err));
    } finally {
      setLoading(false);
    }
  }

  return (
    <DashboardShell>
      <h1 className="mb-6 font-display text-xl font-bold">Departments</h1>
      <GlassCard hover={false} className="mb-6">
        <form onSubmit={handleCreate} className="flex flex-wrap items-end gap-3">
          <input required placeholder="Department name" value={name} onChange={(e) => setName(e.target.value)}
            className="rounded-xl border border-black/10 bg-white/40 px-4 py-2.5 text-sm outline-none dark:border-white/10 dark:bg-white/5" />
          <input placeholder="Description (optional)" value={description} onChange={(e) => setDescription(e.target.value)}
            className="flex-1 rounded-xl border border-black/10 bg-white/40 px-4 py-2.5 text-sm outline-none dark:border-white/10 dark:bg-white/5" />
          <Button type="submit" loading={loading}><Plus size={16} /> Add</Button>
        </form>
        {error && <p className="mt-2 text-sm text-red-600">{error}</p>}
      </GlassCard>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {departments.map((d) => (
          <GlassCard key={d.id} className="flex items-center gap-3">
            <Building2 className="text-[var(--color-primary)]" size={22} />
            <div>
              <p className="font-medium">{d.name}</p>
              <p className="text-xs text-[var(--color-text-muted)]">{d.doctor_count ?? 0} doctors</p>
            </div>
          </GlassCard>
        ))}
      </div>
    </DashboardShell>
  );
}
