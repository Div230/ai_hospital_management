"use client";

import { useEffect, useState } from "react";
import { Plus, Pill } from "lucide-react";
import api, { getApiErrorMessage } from "@/lib/api";
import DashboardShell from "@/components/DashboardShell";
import GlassCard from "@/components/GlassCard";
import Badge from "@/components/Badge";
import Button from "@/components/Button";

interface Medicine {
  id: string;
  name: string;
  generic_name: string;
  price: string;
  stock_quantity: number;
  requires_prescription: boolean;
}

export default function InventoryPage() {
  const [medicines, setMedicines] = useState<Medicine[]>([]);
  const [form, setForm] = useState({ name: "", generic_name: "", price: "", stock_quantity: "" });
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  function load() {
    api.get("/pharmacy/medicines/").then((r) => setMedicines(r.data.results ?? r.data)).catch(() => {});
  }
  useEffect(() => { load(); }, []);

  async function handleAdd(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError("");
    try {
      await api.post("/pharmacy/medicines/", {
        ...form,
        price: parseFloat(form.price),
        stock_quantity: parseInt(form.stock_quantity, 10),
      });
      setForm({ name: "", generic_name: "", price: "", stock_quantity: "" });
      load();
    } catch (err) {
      setError(getApiErrorMessage(err));
    } finally {
      setLoading(false);
    }
  }

  return (
    <DashboardShell>
      <h1 className="mb-6 font-display text-xl font-bold">Inventory</h1>

      <GlassCard hover={false} className="mb-6">
        <form onSubmit={handleAdd} className="grid grid-cols-2 gap-3 sm:grid-cols-4">
          <input required placeholder="Medicine name" value={form.name}
            onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))}
            className="rounded-xl border border-black/10 bg-white/40 px-3 py-2.5 text-sm outline-none dark:border-white/10 dark:bg-white/5" />
          <input placeholder="Generic name" value={form.generic_name}
            onChange={(e) => setForm((f) => ({ ...f, generic_name: e.target.value }))}
            className="rounded-xl border border-black/10 bg-white/40 px-3 py-2.5 text-sm outline-none dark:border-white/10 dark:bg-white/5" />
          <input required type="number" step="0.01" placeholder="Price" value={form.price}
            onChange={(e) => setForm((f) => ({ ...f, price: e.target.value }))}
            className="rounded-xl border border-black/10 bg-white/40 px-3 py-2.5 text-sm outline-none dark:border-white/10 dark:bg-white/5" />
          <input required type="number" placeholder="Stock qty" value={form.stock_quantity}
            onChange={(e) => setForm((f) => ({ ...f, stock_quantity: e.target.value }))}
            className="rounded-xl border border-black/10 bg-white/40 px-3 py-2.5 text-sm outline-none dark:border-white/10 dark:bg-white/5" />
          <Button type="submit" loading={loading} className="col-span-2 sm:col-span-4"><Plus size={16} /> Add medicine</Button>
        </form>
        {error && <p className="mt-2 text-sm text-red-600">{error}</p>}
      </GlassCard>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {medicines.map((m) => (
          <GlassCard key={m.id}>
            <div className="mb-2 flex items-center gap-2">
              <Pill size={18} className="text-[var(--color-primary)]" />
              <p className="font-medium">{m.name}</p>
            </div>
            <p className="text-xs text-[var(--color-text-muted)]">{m.generic_name}</p>
            <div className="mt-3 flex items-center justify-between">
              <span className="font-data text-sm font-bold">₹{m.price}</span>
              <Badge tone={m.stock_quantity > 10 ? "vital" : m.stock_quantity > 0 ? "warn" : "alert"}>
                {m.stock_quantity} in stock
              </Badge>
            </div>
          </GlassCard>
        ))}
      </div>
    </DashboardShell>
  );
}
