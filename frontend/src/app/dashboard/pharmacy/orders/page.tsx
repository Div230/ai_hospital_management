"use client";

import { useEffect, useState } from "react";
import api from "@/lib/api";
import DashboardShell from "@/components/DashboardShell";
import GlassCard from "@/components/GlassCard";
import Badge from "@/components/Badge";

interface Order {
  id: string;
  patient_name: string;
  status: string;
  total_amount: string;
  created_at: string;
}

const STATUS_FLOW = ["PLACED", "CONFIRMED", "PACKED", "OUT_FOR_DELIVERY", "DELIVERED"];

const statusTone: Record<string, "vital" | "warn" | "alert" | "neutral"> = {
  DELIVERED: "vital", PLACED: "warn", CANCELLED: "alert",
};

export default function PharmacyOrdersPage() {
  const [orders, setOrders] = useState<Order[]>([]);

  function load() {
    api.get("/pharmacy/orders/").then((r) => setOrders(r.data.results ?? r.data)).catch(() => {});
  }
  useEffect(() => { load(); }, []);

  async function advanceStatus(order: Order) {
    const idx = STATUS_FLOW.indexOf(order.status);
    if (idx === -1 || idx === STATUS_FLOW.length - 1) return;
    try {
      await api.patch(`/pharmacy/orders/${order.id}/`, { status: STATUS_FLOW[idx + 1] });
      load();
    } catch { /* noop demo */ }
  }

  return (
    <DashboardShell>
      <h1 className="mb-6 font-display text-xl font-bold">Orders</h1>
      <div className="space-y-3">
        {orders.length ? orders.map((o) => (
          <GlassCard key={o.id} className="flex flex-wrap items-center justify-between gap-4">
            <div>
              <p className="font-medium">{o.patient_name}</p>
              <p className="text-xs text-[var(--color-text-muted)]">₹{o.total_amount} · {new Date(o.created_at).toLocaleDateString()}</p>
            </div>
            <div className="flex items-center gap-3">
              <Badge tone={statusTone[o.status] ?? "neutral"}>{o.status.replace(/_/g, " ")}</Badge>
              {STATUS_FLOW.indexOf(o.status) < STATUS_FLOW.length - 1 && (
                <button onClick={() => advanceStatus(o)}
                  className="rounded-lg bg-[var(--color-primary)] px-3 py-1.5 text-xs font-semibold text-white">
                  Advance
                </button>
              )}
            </div>
          </GlassCard>
        )) : (
          <GlassCard className="text-center text-sm text-[var(--color-text-muted)]">No orders yet.</GlassCard>
        )}
      </div>
    </DashboardShell>
  );
}
