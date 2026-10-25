"use client";

import { useState, useEffect } from "react";
import { ShieldCheck, ShieldOff, KeyRound, Bell, BellOff } from "lucide-react";
import api, { getApiErrorMessage } from "@/lib/api";
import { subscribeToPush, unsubscribeFromPush, getPushSubscriptionStatus } from "@/lib/push";
import { useAuth } from "@/context/AuthContext";
import DashboardShell from "@/components/DashboardShell";
import GlassCard from "@/components/GlassCard";
import Button from "@/components/Button";

export default function SettingsPage() {
  const { user } = useAuth();

  const [username, setUsername] = useState(user?.username || "");
  const [usernameMsg, setUsernameMsg] = useState("");
  const [usernameLoading, setUsernameLoading] = useState(false);

  async function handleUsernameUpdate() {
    setUsernameLoading(true);
    setUsernameMsg("");
    try {
      await api.patch("/auth/me/", { username });
      setUsernameMsg("Username updated successfully!");
    } catch (err) {
      setUsernameMsg(getApiErrorMessage(err));
    } finally {
      setUsernameLoading(false);
    }
  }

  const [step, setStep] = useState<"idle" | "setup" | "verify">("idle");
  const [otpauthUri, setOtpauthUri] = useState("");
  const [secret, setSecret] = useState("");
  const [code, setCode] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [loading, setLoading] = useState(false);
  const [is2faEnabled, setIs2faEnabled] = useState(user?.is_2fa_enabled ?? false);
  const [pushStatus, setPushStatus] = useState<"unsupported" | "granted" | "denied" | "default">("default");
  const [pushLoading, setPushLoading] = useState(false);
  const [pushMessage, setPushMessage] = useState("");

  useEffect(() => {
    setUsername(user?.username || "");
    setIs2faEnabled(user?.is_2fa_enabled ?? false);
  }, [user?.id, user?.username, user?.is_2fa_enabled]);

  useEffect(() => {
    getPushSubscriptionStatus().then(setPushStatus);
  }, []);

  async function handleEnablePush() {
    setPushLoading(true);
    setPushMessage("");
    const result = await subscribeToPush();
    setPushMessage(result.message);
    const status = await getPushSubscriptionStatus();
    setPushStatus(status);
    setPushLoading(false);
  }

  async function handleDisablePush() {
    setPushLoading(true);
    setPushMessage("");
    const result = await unsubscribeFromPush();
    setPushMessage(result.message);
    setPushLoading(false);
  }

  async function startSetup() {
    setLoading(true);
    setError("");
    try {
      const { data } = await api.post("/auth/2fa/setup/");
      setOtpauthUri(data.otpauth_uri);
      setSecret(data.secret);
      setStep("verify");
    } catch (err) {
      setError(getApiErrorMessage(err));
    } finally {
      setLoading(false);
    }
  }

  async function confirmEnable() {
    setLoading(true);
    setError("");
    try {
      await api.post("/auth/2fa/enable/", { code });
      setSuccess("2FA enabled successfully.");
      setIs2faEnabled(true);
      setStep("idle");
    } catch (err) {
      setError(getApiErrorMessage(err));
    } finally {
      setLoading(false);
    }
  }

  async function disable2fa() {
    setLoading(true);
    setError("");
    try {
      await api.post("/auth/2fa/disable/", { password });
      setSuccess("2FA disabled.");
      setIs2faEnabled(false);
      setPassword("");
    } catch (err) {
      setError(getApiErrorMessage(err));
    } finally {
      setLoading(false);
    }
  }

  return (
    <DashboardShell>
      <h1 className="mb-6 font-display text-xl font-bold">Settings</h1>

      <div className="grid gap-6 lg:grid-cols-2">
        <GlassCard hover={false}>
          <div className="mb-2 flex items-center gap-2">
            <KeyRound size={18} className="text-[var(--color-primary)]" />
            <h2 className="font-display font-semibold">Account</h2>
          </div>
          <div className="space-y-2 text-sm">
            <p><span className="text-[var(--color-text-muted)]">Name:</span> {user?.first_name} {user?.last_name}</p>
            <p><span className="text-[var(--color-text-muted)]">Email:</span> {user?.email}</p>
            <p><span className="text-[var(--color-text-muted)]">Role:</span> {user?.role?.replace("_", " ")}</p>
          </div>

          <div className="mt-4 border-t border-black/10 pt-4 dark:border-white/10">
            <label className="mb-1.5 block text-sm font-medium">Username</label>
            <div className="flex gap-2">
              <input
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                className="flex-1 rounded-xl border border-black/10 bg-white/40 px-4 py-2 text-sm outline-none dark:border-white/10 dark:bg-white/5"
              />
              <Button onClick={handleUsernameUpdate} loading={usernameLoading}>Save</Button>
            </div>
            {usernameMsg && <p className="mt-2 text-sm text-[var(--color-text-muted)]">{usernameMsg}</p>}
          </div>
        </GlassCard>

        <GlassCard hover={false}>
          <div className="mb-2 flex items-center gap-2">
            {is2faEnabled ? <ShieldCheck size={18} className="text-[var(--color-vital)]" /> : <ShieldOff size={18} className="text-[var(--color-text-muted)]" />}
            <h2 className="font-display font-semibold">Two-Factor Authentication</h2>
          </div>
          <p className="mb-4 text-sm text-[var(--color-text-muted)]">
            Add an extra layer of security using an authenticator app (Google Authenticator, Authy, etc).
          </p>

          {error && <p className="mb-3 text-sm text-red-600">{error}</p>}
          {success && <p className="mb-3 text-sm text-[var(--color-vital)]">{success}</p>}

          {step === "idle" && !is2faEnabled && (
            <Button onClick={startSetup} loading={loading}>Enable 2FA</Button>
          )}

          {step === "verify" && (
            <div className="space-y-3">
              <div className="rounded-xl bg-black/[0.03] p-3 text-xs dark:bg-white/[0.05]">
                <p className="mb-1 text-[var(--color-text-muted)]">Manual entry key (if you can&apos;t scan a QR):</p>
                <p className="break-all font-data">{secret}</p>
                <p className="mt-2 break-all text-[var(--color-text-muted)]">{otpauthUri}</p>
              </div>
              <input
                placeholder="Enter 6-digit code from your app"
                value={code}
                onChange={(e) => setCode(e.target.value)}
                className="w-full rounded-xl border border-black/10 bg-white/40 px-4 py-2.5 text-sm outline-none dark:border-white/10 dark:bg-white/5"
              />
              <Button onClick={confirmEnable} loading={loading} className="w-full">Confirm & enable</Button>
            </div>
          )}

          {is2faEnabled && (
            <div className="space-y-3">
              <input
                type="password"
                placeholder="Enter password to disable"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full rounded-xl border border-black/10 bg-white/40 px-4 py-2.5 text-sm outline-none dark:border-white/10 dark:bg-white/5"
              />
              <Button variant="danger" onClick={disable2fa} loading={loading}>Disable 2FA</Button>
            </div>
          )}
        </GlassCard>

        <GlassCard hover={false}>
          <div className="mb-2 flex items-center gap-2">
            {pushStatus === "granted" ? <Bell size={18} className="text-[var(--color-vital)]" /> : <BellOff size={18} className="text-[var(--color-text-muted)]" />}
            <h2 className="font-display font-semibold">Push Notifications</h2>
          </div>
          <p className="mb-4 text-sm text-[var(--color-text-muted)]">
            Get real-time browser alerts for appointments, lab reports, and prescription updates —
            even when this tab isn&apos;t open.
          </p>
          {pushMessage && <p className="mb-3 text-sm text-[var(--color-text-muted)]">{pushMessage}</p>}

          {pushStatus === "unsupported" && (
            <p className="text-sm text-[var(--color-alert)]">Your browser doesn&apos;t support push notifications.</p>
          )}
          {pushStatus !== "unsupported" && (
            <Button
              variant={pushStatus === "granted" ? "secondary" : "primary"}
              onClick={pushStatus === "granted" ? handleDisablePush : handleEnablePush}
              loading={pushLoading}
            >
              {pushStatus === "granted" ? "Disable push notifications" : "Enable push notifications"}
            </Button>
          )}
        </GlassCard>
      </div>
      <GlassCard hover={false} className="mt-6 border-red-400/30 bg-red-500/5">
        <h2 className="mb-2 font-display font-semibold text-[var(--color-alert)]">Danger Zone</h2>
        <p className="mb-4 text-sm text-[var(--color-text-muted)]">
          Account deletion requires hospital review of clinical record retention. Contact the hospital administrator.
        </p>
        <Button variant="danger" disabled title="Account deletion requires hospital retention review">
          Delete My Account
        </Button>
      </GlassCard>
    </DashboardShell>
  );
}
