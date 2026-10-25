"use client";

import { useEffect, useState } from "react";
import { Upload, FileText, Activity, ShieldAlert, Loader2 } from "lucide-react";
import api, { getApiErrorMessage } from "@/lib/api";
import DashboardShell from "@/components/DashboardShell";
import GlassCard from "@/components/GlassCard";
import Badge from "@/components/Badge";
import Button from "@/components/Button";

interface MedicalReport {
  id: string;
  report_type: string;
  status: string;
  file: string;
  ai_structured_summary: { summary?: string };
  ai_abnormal_values: string[];
  created_at: string;
}

interface HistoryEntry {
  id: string;
  entry_type: string;
  title: string;
  description: string;
  date_occurred: string;
}

interface RiskPrediction {
  id: string;
  condition_name: string;
  risk_percentage: string;
  recommendation: string;
}

const statusTone: Record<string, "vital" | "warn" | "alert" | "neutral"> = {
  ANALYZED: "vital", PROCESSING: "warn", FAILED: "alert", UPLOADED: "neutral",
};

export default function MedicalRecordsPage() {
  const [reports, setReports] = useState<MedicalReport[]>([]);
  const [history, setHistory] = useState<HistoryEntry[]>([]);
  const [risks, setRisks] = useState<RiskPrediction[]>([]);
  const [reportType, setReportType] = useState("BLOOD");
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState("");
  const [riskLoading, setRiskLoading] = useState(false);

  function loadAll() {
    api.get("/patients/medical-reports/").then((r) => setReports(r.data.results ?? r.data)).catch(() => {});
    api.get("/patients/medical-history/").then((r) => setHistory(r.data.results ?? r.data)).catch(() => {});
    api.get("/ai/disease-risk/").then((r) => setRisks(r.data.data ?? [])).catch(() => {});
  }

  useEffect(() => { loadAll(); }, []);

  // Auto-refresh every 3 seconds while any report is still being analyzed
  // (OCR + AI takes a few seconds), so the status updates without a manual refresh.
  useEffect(() => {
    const hasPending = reports.some((r) => r.status === "UPLOADED" || r.status === "PROCESSING");
    if (!hasPending) return;

    const interval = setInterval(() => {
      api.get("/patients/medical-reports/").then((r) => setReports(r.data.results ?? r.data)).catch(() => {});
    }, 3000);

    return () => clearInterval(interval);
  }, [reports]);

  async function handleUpload(e: React.FormEvent) {
    e.preventDefault();
    if (!file) return;
    setUploading(true);
    setError("");

    // Optimistic placeholder — shows a spinner card immediately, since the
    // actual OCR+AI analysis runs synchronously (no Celery worker) and can
    // take several seconds before the real report appears from the server.
    const tempId = `temp-${Date.now()}`;
    setReports((prev) => [
      {
        id: tempId,
        report_type: reportType,
        status: "PROCESSING",
        file: "",
        ai_structured_summary: {},
        ai_abnormal_values: [],
        created_at: new Date().toISOString(),
      },
      ...prev,
    ]);

    try {
      const formData = new FormData();
      formData.append("report_type", reportType);
      formData.append("file", file);
      await api.post("/patients/medical-reports/", formData);
      setFile(null);
    } catch (err) {
      setError(getApiErrorMessage(err));
    } finally {
      setUploading(false);
      loadAll(); // replaces the temp placeholder with the real, final report from the server
    }
  }

  async function runRiskPrediction() {
    if (!window.confirm("This request sends your profile and recent report summaries to the configured external AI provider. Do you authorize this?")) return;
    setRiskLoading(true);
    try {
      const { data } = await api.post("/ai/disease-risk/", {}, { headers: { "X-AI-Consent": "true" } });
      setRisks(data.data ?? []);
    } catch (err) {
      setError(getApiErrorMessage(err));
    } finally {
      setRiskLoading(false);
    }
  }

  return (
    <DashboardShell>
      <h1 className="mb-6 font-display text-xl font-bold">Medical Records</h1>

      <div className="grid gap-6 lg:grid-cols-3">
        <GlassCard className="lg:col-span-2">
          <div className="mb-4 flex items-center gap-2">
            <Upload size={18} className="text-[var(--color-primary)]" />
            <h2 className="font-display font-semibold">Upload a report</h2>
            <Badge tone="accent">Local OCR only</Badge>
          </div>
          <form onSubmit={handleUpload} className="flex flex-wrap items-end gap-3">
            <select value={reportType} onChange={(e) => setReportType(e.target.value)}
              className="rounded-xl border border-black/10 bg-white/40 px-4 py-2.5 text-sm outline-none dark:border-white/10 dark:bg-white/5">
              <option value="BLOOD">Blood Test</option>
              <option value="XRAY">X-Ray</option>
              <option value="MRI">MRI</option>
              <option value="CT">CT Scan</option>
              <option value="PRESCRIPTION">Prescription</option>
              <option value="OTHER">Other</option>
            </select>
            <input type="file" accept=".pdf,.png,.jpg,.jpeg"
              onChange={(e) => setFile(e.target.files?.[0] ?? null)}
              className="text-sm" />
            <Button type="submit" loading={uploading} disabled={!file}>Upload</Button>
          </form>
          {error && <p className="mt-2 text-sm text-red-600">{error}</p>}

          <div className="mt-6 space-y-3">
            {reports.length ? reports.map((r) => (
              <div key={r.id} className="rounded-xl bg-black/[0.02] p-4 dark:bg-white/[0.03]">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <FileText size={16} className="text-[var(--color-text-muted)]" />
                    <p className="text-sm font-medium">{r.report_type.replace("_", " ")}</p>
                  </div>
                  <Badge tone={statusTone[r.status] ?? "neutral"}>{r.status}</Badge>
                </div>
                {(r.status === "UPLOADED" || r.status === "PROCESSING") && (
                  <div className="mt-2 flex items-center gap-2 text-xs text-[var(--color-text-muted)]">
                    <Loader2 size={13} className="animate-spin" />
                    Analyzing report with OCR + AI...
                  </div>
                )}
                {r.ai_structured_summary?.summary && (
                  <p className="mt-2 text-xs text-[var(--color-text-muted)]">{r.ai_structured_summary.summary}</p>
                )}
                {!!r.ai_abnormal_values?.length && (
                  <div className="mt-2 flex flex-wrap gap-1.5">
                    {r.ai_abnormal_values.map((v, i) => <Badge key={i} tone="warn">{v}</Badge>)}
                  </div>
                )}
              </div>
            )) : (
              <p className="rounded-xl border border-dashed border-black/10 p-6 text-center text-sm text-[var(--color-text-muted)] dark:border-white/10">
                No reports uploaded yet.
              </p>
            )}
          </div>
        </GlassCard>

        <div className="space-y-6">
          <GlassCard>
            <div className="mb-3 flex items-center gap-2">
              <ShieldAlert size={18} className="text-[var(--color-primary)]" />
              <h2 className="font-display font-semibold">AI Disease Risk</h2>
            </div>
            <Button variant="secondary" onClick={runRiskPrediction} loading={riskLoading} className="mb-4 w-full">
              Run risk screening
            </Button>
            <div className="space-y-3">
              {risks.length ? risks.map((r) => (
                <div key={r.id} className="rounded-xl bg-black/[0.02] p-3 dark:bg-white/[0.03]">
                  <div className="flex items-center justify-between">
                    <p className="text-sm font-medium">{r.condition_name}</p>
                    <span className="font-data text-sm font-bold text-[var(--color-warn)]">{r.risk_percentage}%</span>
                  </div>
                  <p className="mt-1 text-xs text-[var(--color-text-muted)]">{r.recommendation}</p>
                </div>
              )) : (
                <p className="text-xs text-[var(--color-text-muted)]">No screening run yet.</p>
              )}
            </div>
          </GlassCard>

          <GlassCard>
            <div className="mb-3 flex items-center gap-2">
              <Activity size={18} className="text-[var(--color-primary)]" />
              <h2 className="font-display font-semibold">History timeline</h2>
            </div>
            <div className="space-y-3">
              {history.length ? history.map((h) => (
                <div key={h.id} className="border-l-2 border-[var(--color-primary)]/30 pl-3">
                  <p className="text-xs text-[var(--color-text-muted)]">{h.date_occurred}</p>
                  <p className="text-sm font-medium">{h.title}</p>
                  <Badge tone="neutral">{h.entry_type}</Badge>
                </div>
              )) : (
                <p className="text-xs text-[var(--color-text-muted)]">No history entries yet.</p>
              )}
            </div>
          </GlassCard>
        </div>
      </div>
    </DashboardShell>
  );
}
