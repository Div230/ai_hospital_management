"use client";

import { useEffect, useState } from "react";
import { Upload, FlaskConical } from "lucide-react";
import api, { getApiErrorMessage } from "@/lib/api";
import DashboardShell from "@/components/DashboardShell";
import GlassCard from "@/components/GlassCard";
import Badge from "@/components/Badge";
import Button from "@/components/Button";

interface TestRequest {
  id: string;
  patient_name: string;
  test_type: string;
  test_name: string;
  status: string;
}

const statusTone: Record<string, "vital" | "warn" | "alert" | "neutral" | "accent"> = {
  COMPLETED: "vital", REQUESTED: "warn", IN_PROGRESS: "accent", CANCELLED: "alert",
};

export default function LabRequestsPage() {
  const [requests, setRequests] = useState<TestRequest[]>([]);
  const [uploadingId, setUploadingId] = useState<string | null>(null);
  const [error, setError] = useState("");

  function load() {
    api.get("/laboratory/test-requests/").then((r) => setRequests(r.data.results ?? r.data)).catch(() => {});
  }
  useEffect(() => { load(); }, []);

  async function handleFileUpload(requestId: string, file: File) {
    setUploadingId(requestId);
    setError("");
    try {
      const formData = new FormData();
      formData.append("file", file);
      await api.post(`/laboratory/test-requests/${requestId}/upload-report/`, formData);
      load();
    } catch (err) {
      setError(getApiErrorMessage(err));
    } finally {
      setUploadingId(null);
    }
  }

  return (
    <DashboardShell>
      <h1 className="mb-6 font-display text-xl font-bold">Test Requests</h1>
      {error && <p className="mb-4 text-sm text-red-600">{error}</p>}
      <div className="space-y-3">
        {requests.length ? requests.map((r) => (
          <GlassCard key={r.id} className="flex flex-wrap items-center justify-between gap-4">
            <div className="flex items-center gap-3">
              <FlaskConical className="text-[var(--color-primary)]" size={20} />
              <div>
                <p className="font-medium">{r.test_name} ({r.test_type})</p>
                <p className="text-xs text-[var(--color-text-muted)]">Patient: {r.patient_name}</p>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <Badge tone={statusTone[r.status] ?? "neutral"}>{r.status.replace("_", " ")}</Badge>
              {r.status !== "COMPLETED" && (
                <label className="cursor-pointer">
                  <input type="file" className="hidden" accept=".pdf,.png,.jpg,.jpeg"
                    onChange={(e) => e.target.files?.[0] && handleFileUpload(r.id, e.target.files[0])} />
                  <span className="flex items-center gap-1.5 rounded-xl bg-[var(--color-primary)] px-3 py-1.5 text-xs font-semibold text-white">
                    <Upload size={13} /> {uploadingId === r.id ? "Uploading..." : "Upload report"}
                  </span>
                </label>
              )}
            </div>
          </GlassCard>
        )) : (
          <GlassCard className="text-center text-sm text-[var(--color-text-muted)]">No test requests yet.</GlassCard>
        )}
      </div>
    </DashboardShell>
  );
}
