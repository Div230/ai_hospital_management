"use client";
import DashboardShell from "@/components/DashboardShell";
import GlassCard from "@/components/GlassCard";
export default function Page() {
  return <DashboardShell><GlassCard hover={false}><h1 className="font-display text-xl font-bold">Emergency assistance</h1><p className="mt-4">Ambulance dispatch is unavailable. Contact your local emergency service directly. This application does not dispatch an ambulance.</p><a className="mt-5 inline-block rounded-xl bg-red-600 px-5 py-3 font-semibold text-white" href="tel:112">Call 112 — India emergency assistance</a></GlassCard></DashboardShell>;
}
