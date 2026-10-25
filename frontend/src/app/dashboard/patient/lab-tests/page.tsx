"use client";

import { useEffect, useState } from "react";
import { FlaskConical, Plus } from "lucide-react";
import api, { getApiErrorMessage } from "@/lib/api";
import DashboardShell from "@/components/DashboardShell";
import GlassCard from "@/components/GlassCard";
import Badge from "@/components/Badge";
import Button from "@/components/Button";

function getFullFileUrl(path: string) {
  const apiBase = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api";
  const backendBase = apiBase.replace(/\/api\/?$/, "");
  return path.startsWith("http") ? path : `${backendBase}${path}`;
}

interface Laboratory {
  id: string;
  name: string;
  city: string;
}

interface TestRequest {
  id: string;
  test_type: string;
  test_name: string;
  status: string;
  report?: {
    result_summary: string;
    ai_abnormal_findings: string[];
    file_url: string | null;
  } | null;
}

const statusTone: Record<string, "vital" | "warn" | "alert" | "neutral"> = {
  COMPLETED: "vital", REQUESTED: "warn", IN_PROGRESS: "neutral", CANCELLED: "alert",
};

export default function LabTestsPage() {
  const [labs, setLabs] = useState<Laboratory[]>([]);
  const [requests, setRequests] = useState<TestRequest[]>([]);
  const [labId, setLabId] = useState("");
  const [testType, setTestType] = useState("BLOOD");
  const [testName, setTestName] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  function loadAll() {
    api.get("/laboratory/directory/").then((r) => setLabs(r.data.results ?? r.data)).catch(() => {});
    api.get("/laboratory/test-requests/").then((r) => setRequests(r.data.results ?? r.data)).catch(() => {});
  }

  useEffect(() => { loadAll(); }, []);

  async function handleBook(e: React.FormEvent) {
    e.preventDefault();
    if (!labId || !testName) return;
    setLoading(true);
    setError("");
    try {
      await api.post("/laboratory/test-requests/", {
        laboratory: labId, test_type: testType, test_name: testName,
      });
      setTestName("");
      loadAll();
    } catch (err) {
      setError(getApiErrorMessage(err));
    } finally {
      setLoading(false);
    }
  }

  return (
    <DashboardShell>
      <h1 className="mb-6 font-display text-xl font-bold">Lab Tests</h1>

      <div className="grid gap-6 lg:grid-cols-2">
        <GlassCard hover={false}>
          <div className="mb-4 flex items-center gap-2">
            <FlaskConical size={18} className="text-[var(--color-primary)]" />
            <h2 className="font-display font-semibold">Book a lab test</h2>
          </div>
          {error && <p className="mb-3 text-sm text-red-600">{error}</p>}
          <form onSubmit={handleBook} className="space-y-4">
            <select required value={labId} onChange={(e) => setLabId(e.target.value)}
              className="w-full rounded-xl border border-black/10 bg-white/40 px-4 py-2.5 text-sm outline-none dark:border-white/10 dark:bg-white/5">
              <option value="">Select a laboratory...</option>
              {labs.map((l) => (
                <option key={l.id} value={l.id}>{l.name} {l.city ? `— ${l.city}` : ""}</option>
              ))}
            </select>
            <select value={testType} onChange={(e) => setTestType(e.target.value)}
              className="w-full rounded-xl border border-black/10 bg-white/40 px-4 py-2.5 text-sm outline-none dark:border-white/10 dark:bg-white/5">
              <option value="BLOOD">Blood Test</option>
              <option value="XRAY">X-Ray</option>
              <option value="MRI">MRI</option>
              <option value="CT">CT Scan</option>
              <option value="OTHER">Other</option>
            </select>
            <input required placeholder="Test name (e.g. CBC, Chest X-Ray)" value={testName}
              onChange={(e) => setTestName(e.target.value)}
              className="w-full rounded-xl border border-black/10 bg-white/40 px-4 py-2.5 text-sm outline-none dark:border-white/10 dark:bg-white/5" />
            <Button type="submit" loading={loading} className="w-full">
              <Plus size={16} /> Book test
            </Button>
          </form>
          {!labs.length && (
            <p className="mt-3 text-xs text-[var(--color-text-muted)]">
              No verified laboratories yet — a hospital admin needs to verify one first.
            </p>
          )}
        </GlassCard>

        <GlassCard>
          <h2 className="mb-4 font-display font-semibold">My test requests</h2>
          <div className="space-y-3">
            {requests.length ? requests.map((r) => (
              <div key={r.id} className="rounded-xl bg-black/[0.02] p-3 dark:bg-white/[0.03]">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium">{r.test_name}</p>
                    <p className="text-xs text-[var(--color-text-muted)]">{r.test_type}</p>
                  </div>
                  <Badge tone={statusTone[r.status] ?? "neutral"}>{r.status.replace("_", " ")}</Badge>
                </div>
                {r.report && (
                  <div className="mt-3 border-t border-black/10 pt-3 dark:border-white/10">
                    {r.report.result_summary && (
                      <p className="text-xs text-[var(--color-text-muted)]">{r.report.result_summary}</p>
                    )}
                    {!!r.report.ai_abnormal_findings?.length && (
                      <div className="mt-2 flex flex-wrap gap-1.5">
                        {r.report.ai_abnormal_findings.map((f, i) => <Badge key={i} tone="warn">{f}</Badge>)}
                      </div>
                    )}
                    {r.report.file_url && (
                      <div className="mt-2 flex gap-3">
                        <a href={getFullFileUrl(r.report.file_url)} target="_blank" rel="noopener noreferrer"
                          className="text-xs font-medium text-[var(--color-primary)] hover:underline">
                          View report
                        </a>
                        <a href={getFullFileUrl(r.report.file_url)} download
                          className="text-xs font-medium text-[var(--color-primary)] hover:underline">
                          Download report
                        </a>
                      </div>
                    )}
                  </div>
                )}
              </div>
            )) : (
              <p className="text-sm text-[var(--color-text-muted)]">No test requests yet.</p>
            )}
          </div>
        </GlassCard>
      </div>
    </DashboardShell>
  );
}
