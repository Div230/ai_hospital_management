"use client";

import { useState } from "react";
import Link from "next/link";
import { HeartPulse, Mail, Lock } from "lucide-react";
import { useAuth } from "@/context/AuthContext";
import GlassCard from "@/components/GlassCard";
import Button from "@/components/Button";
import EkgLine from "@/components/EkgLine";

export default function LoginPage() {
  const { login, verify2fa } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [needs2fa, setNeeds2fa] = useState<{ challenge: string } | null>(null);
  const [code, setCode] = useState("");

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const result = await login(email, password);
      if (result.requires2fa && result.challenge) {
        setNeeds2fa({ challenge: result.challenge });
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Login failed.");
    } finally {
      setLoading(false);
    }
  }

  async function handleVerify2fa(e: React.FormEvent) {
    e.preventDefault();
    if (!needs2fa) return;
    setError("");
    setLoading(true);
    try {
      await verify2fa(needs2fa.challenge, code);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Invalid code.");
    } finally {
      setLoading(false);
    }
  }

  if (needs2fa) {
    return (
      <div className="flex min-h-screen items-center justify-center px-6">
        <GlassCard hover={false} className="w-full max-w-md">
          <div className="mb-6 text-center">
            <h1 className="font-display text-2xl font-bold">Two-Factor Verification</h1>
            <p className="text-sm text-[var(--color-text-muted)]">Enter the code from your authenticator app</p>
          </div>
          {error && (
            <div className="mb-4 rounded-xl bg-red-500/10 px-4 py-3 text-sm text-red-600 dark:text-red-400">
              {error}
            </div>
          )}
          <form onSubmit={handleVerify2fa} className="space-y-4">
            <input
              value={code}
              onChange={(e) => setCode(e.target.value)}
              placeholder="6-digit code"
              className="w-full rounded-xl border border-black/10 bg-white/40 px-4 py-2.5 text-center text-lg tracking-widest outline-none focus:border-[var(--color-primary)] dark:border-white/10 dark:bg-white/5"
            />
            <Button type="submit" loading={loading} className="w-full">Verify & log in</Button>
          </form>
        </GlassCard>
      </div>
    );
  }

  return (
    <div className="flex min-h-screen items-center justify-center px-6">
      <GlassCard hover={false} className="w-full max-w-md">
        <div className="mb-6 flex flex-col items-center text-center">
          <Link href="/" className="mb-4 flex items-center gap-2 font-display text-lg font-bold text-[var(--color-primary)]">
            <HeartPulse className="text-[var(--color-accent)]" size={22} /> AIHMS
          </Link>
          <EkgLine width={220} height={40} />
          <h1 className="mt-2 font-display text-2xl font-bold">Welcome back</h1>
          <p className="text-sm text-[var(--color-text-muted)]">Log in to your care dashboard</p>
        </div>

        {error && (
          <div className="mb-4 rounded-xl bg-red-500/10 px-4 py-3 text-sm text-red-600 dark:text-red-400">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="mb-1.5 block text-sm font-medium">Email</label>
            <div className="relative">
              <Mail className="absolute left-3 top-1/2 -translate-y-1/2 text-[var(--color-text-muted)]" size={17} />
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="you@example.com"
                className="w-full rounded-xl border border-black/10 bg-white/40 py-2.5 pl-10 pr-4 text-sm outline-none focus:border-[var(--color-primary)] dark:border-white/10 dark:bg-white/5"
              />
            </div>
          </div>
          <div>
            <label className="mb-1.5 block text-sm font-medium">Password</label>
            <div className="relative">
              <Lock className="absolute left-3 top-1/2 -translate-y-1/2 text-[var(--color-text-muted)]" size={17} />
              <input
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                className="w-full rounded-xl border border-black/10 bg-white/40 py-2.5 pl-10 pr-4 text-sm outline-none focus:border-[var(--color-primary)] dark:border-white/10 dark:bg-white/5"
              />
            </div>
            <div className="mt-2 text-right">
              <Link href="/forgot-password" className="text-xs text-[var(--color-primary)] hover:underline">
                Forgot password?
              </Link>
            </div>
          </div>
          <Button type="submit" loading={loading} className="w-full">
            Log in
          </Button>
        </form>

        <p className="mt-6 text-center text-sm text-[var(--color-text-muted)]">
          Don&apos;t have an account?{" "}
          <Link href="/register" className="font-medium text-[var(--color-primary)] hover:underline">
            Register
          </Link>
        </p>
      </GlassCard>
    </div>
  );
}
