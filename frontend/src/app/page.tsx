import Link from "next/link";
import { HeartPulse, Stethoscope, Building2, FlaskConical, Pill, FileText, ShieldCheck } from "lucide-react";
import GlassCard from "@/components/GlassCard";

const roles = [
  { icon: HeartPulse, title: "Patients", desc: "Find doctors, book available appointments, and access your own records." },
  { icon: Stethoscope, title: "Doctors", desc: "Manage assigned consultations, clinical notes, and digital prescriptions." },
  { icon: Building2, title: "Hospital administration", desc: "Manage your hospital, departments, and doctor assignments." },
  { icon: FlaskConical, title: "Laboratories", desc: "Receive assigned requests and upload patient reports." },
  { icon: Pill, title: "Pharmacies", desc: "Manage your inventory and assigned orders." },
];
export default function Home() {
  return <div className="mx-auto flex w-full max-w-6xl flex-1 flex-col px-6">
    <nav className="flex items-center justify-between py-6"><Link href="/" className="flex items-center gap-2 font-display text-lg font-bold text-[var(--color-primary)]"><HeartPulse size={24} />AIHMS</Link><div className="flex gap-4 text-sm"><Link href="/login" className="rounded-xl px-4 py-3">Log in</Link><Link href="/register" className="rounded-xl bg-[var(--color-primary)] px-4 py-3 font-semibold text-white">Get started</Link></div></nav>
    <section className="grid items-center gap-12 py-16 md:grid-cols-2"><div><p className="mb-4 text-sm font-semibold uppercase tracking-widest text-teal-700 dark:text-teal-300">AI Hospital Management System</p><h1 className="font-display text-5xl font-bold leading-tight tracking-tight">Connected care.<br /><span className="text-[var(--color-primary)]">One patient portal.</span></h1><p className="mt-6 max-w-lg text-lg text-[var(--color-text-muted)]">A shared platform for patients, doctors, hospital teams, laboratories, and pharmacies. Keep your appointments and medical documents within reach.</p><Link href="/register" className="mt-8 inline-flex rounded-xl bg-[var(--color-primary)] px-6 py-3 font-semibold text-white">Create your patient account →</Link></div><GlassCard hover={false}><FileText className="mb-5 text-teal-600" size={40} /><h2 className="font-display text-2xl font-semibold">Read your prescription more clearly.</h2><p className="mt-4 text-[var(--color-text-muted)]">Upload a printed prescription for local OCR, or use an operator-configured model for handwriting. Compare the transcription with the original, see uncertainty, and request review from your treating doctor.</p><div className="mt-6 flex items-start gap-3 rounded-xl bg-amber-500/10 p-4 text-sm"><ShieldCheck className="shrink-0" size={20} /><p>Transcription is unverified. Always check medicines and doses with a licensed clinician or pharmacist.</p></div><Link href="/login" className="mt-6 inline-block font-semibold text-[var(--color-primary)]">Open prescription reader →</Link></GlassCard></section>
    <section className="pb-16"><h2 className="mb-6 font-display text-2xl font-semibold">A workspace for every care team</h2><div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">{roles.map(({ icon: Icon, title, desc }) => <GlassCard key={title}><Icon className="mb-4 text-[var(--color-primary)]" size={26} /><h3 className="font-semibold">{title}</h3><p className="mt-2 text-sm text-[var(--color-text-muted)]">{desc}</p></GlassCard>)}</div></section>
    <footer className="border-t border-black/10 py-6 text-sm text-[var(--color-text-muted)] dark:border-white/10">AIHMS · Hospital operations and prescription transcription. Emergency dispatch is unavailable.</footer>
  </div>;
}
