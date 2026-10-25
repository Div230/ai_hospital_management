"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { HeartPulse, User, Stethoscope, Building2, FlaskConical, Pill, CheckCircle2 } from "lucide-react";
import { useAuth } from "@/context/AuthContext";
import GlassCard from "@/components/GlassCard";
import Button from "@/components/Button";
import clsx from "clsx";

const ROLE_OPTIONS = [{ value: "patient", label: "Patient", icon: User }];

export default function RegisterPage() {
  const { register } = useAuth();
  const router = useRouter();
  const [form, setForm] = useState({
    role: "patient",
    first_name: "",
    last_name: "",
    username: "",
    email: "",
    phone_number: "",
    password: "",
    password_confirm: "",
  });
  const [error, setError] = useState("");
  const [success, setSuccess] = useState(false);
  const [loading, setLoading] = useState(false);

  function update<K extends keyof typeof form>(key: K, value: string) {
    setForm((f) => ({ ...f, [key]: value }));
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const formattedPhone = form.phone_number && !form.phone_number.startsWith("+")
        ? `+91${form.phone_number}`
        : form.phone_number;
      await register({ ...form, phone_number: formattedPhone });
      setSuccess(true);
      setTimeout(() => router.push("/login"), 1800);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Registration failed.");
    } finally {
      setLoading(false);
    }
  }

  if (success) {
    return (
      <div className="flex min-h-screen items-center justify-center px-6">
        <GlassCard hover={false} className="w-full max-w-md text-center">
          <CheckCircle2 className="mx-auto mb-4 text-[var(--color-vital)]" size={48} />
          <h1 className="font-display text-xl font-bold">Account created!</h1>
          <p className="mt-2 text-sm text-[var(--color-text-muted)]">
            Check your email to verify your account. Redirecting to login…
          </p>
        </GlassCard>
      </div>
    );
  }

  return (
    <div className="flex min-h-screen items-center justify-center px-6 py-12">
      <GlassCard hover={false} className="w-full max-w-lg">
        <div className="mb-6 text-center">
          <Link href="/" className="mb-2 inline-flex items-center gap-2 font-display text-lg font-bold text-[var(--color-primary)]">
            <HeartPulse className="text-[var(--color-accent)]" size={22} /> AIHMS
          </Link>
          <h1 className="font-display text-2xl font-bold">Create your account</h1>
          <p className="text-sm text-[var(--color-text-muted)]">Create a patient account. Staff accounts are provisioned by the hospital.</p>
        </div>

        {error && (
          <div className="mb-4 rounded-xl bg-red-500/10 px-4 py-3 text-sm text-red-600 dark:text-red-400">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-5">
          <div className="grid grid-cols-1 gap-2">
            {ROLE_OPTIONS.map((r) => (
              <button
                type="button"
                key={r.value}
                onClick={() => update("role", r.value)}
                className={clsx(
                  "flex flex-col items-center gap-1.5 rounded-xl border p-3 text-xs font-medium transition-colors",
                  form.role === r.value
                    ? "border-[var(--color-primary)] bg-[var(--color-primary)]/10 text-[var(--color-primary)]"
                    : "border-black/10 text-[var(--color-text-muted)] dark:border-white/10"
                )}
              >
                <r.icon size={18} />
                {r.label}
              </button>
            ))}
          </div>

          <div className="grid grid-cols-2 gap-4">
            <input required placeholder="First name" value={form.first_name}
              onChange={(e) => update("first_name", e.target.value)}
              className="rounded-xl border border-black/10 bg-white/40 px-4 py-2.5 text-sm outline-none focus:border-[var(--color-primary)] dark:border-white/10 dark:bg-white/5" />
            <input required placeholder="Last name" value={form.last_name}
              onChange={(e) => update("last_name", e.target.value)}
              className="rounded-xl border border-black/10 bg-white/40 px-4 py-2.5 text-sm outline-none focus:border-[var(--color-primary)] dark:border-white/10 dark:bg-white/5" />
          </div>
          <input required placeholder="Username" value={form.username}
            onChange={(e) => update("username", e.target.value)}
            className="w-full rounded-xl border border-black/10 bg-white/40 px-4 py-2.5 text-sm outline-none focus:border-[var(--color-primary)] dark:border-white/10 dark:bg-white/5" />
          <input required type="email" placeholder="Email address" value={form.email}
            onChange={(e) => update("email", e.target.value)}
            className="w-full rounded-xl border border-black/10 bg-white/40 px-4 py-2.5 text-sm outline-none focus:border-[var(--color-primary)] dark:border-white/10 dark:bg-white/5" />
          <input placeholder="+91XXXXXXXXXX (with country code)" value={form.phone_number}
            onChange={(e) => update("phone_number", e.target.value)}
            className="w-full rounded-xl border border-black/10 bg-white/40 px-4 py-2.5 text-sm outline-none focus:border-[var(--color-primary)] dark:border-white/10 dark:bg-white/5" />
          <div className="grid grid-cols-2 gap-4">
            <input required type="password" placeholder="Password" value={form.password}
              onChange={(e) => update("password", e.target.value)}
              className="rounded-xl border border-black/10 bg-white/40 px-4 py-2.5 text-sm outline-none focus:border-[var(--color-primary)] dark:border-white/10 dark:bg-white/5" />
            <input required type="password" placeholder="Confirm password" value={form.password_confirm}
              onChange={(e) => update("password_confirm", e.target.value)}
              className="rounded-xl border border-black/10 bg-white/40 px-4 py-2.5 text-sm outline-none focus:border-[var(--color-primary)] dark:border-white/10 dark:bg-white/5" />
          </div>

          <Button type="submit" loading={loading} className="w-full">
            Create account
          </Button>
        </form>

        <p className="mt-6 text-center text-sm text-[var(--color-text-muted)]">
          Already have an account?{" "}
          <Link href="/login" className="font-medium text-[var(--color-primary)] hover:underline">
            Log in
          </Link>
        </p>
      </GlassCard>
    </div>
  );
}
