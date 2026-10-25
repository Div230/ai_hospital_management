"use client";

import { useEffect, useRef, useState } from "react";
import { UploadCloud, FileText, RefreshCw, Copy, Download, AlertTriangle } from "lucide-react";
import api, { getApiErrorMessage } from "@/lib/api";
import { useAuth } from "@/context/AuthContext";
import DashboardShell from "@/components/DashboardShell";
import GlassCard from "@/components/GlassCard";
import Button from "@/components/Button";

interface Field { field: string; value: string | null; status: "uncertain" | "unreadable" | "not_present"; page: number | null; evidence: string; }
interface Review { id: number; doctor_name: string; notes: string; created_at: string; }
interface Upload {
  id: string; patient_name: string; original_filename: string; mime_type: string; status: string;
  error_message: string; file_url: string; recognition_mode: string; created_at: string;
  result: { transcription?: string; fields?: Field[]; notice?: string; readability?: string; provider?: string };
  personal_correction: { text: string } | null; reviews: Review[]; review_requested_at: string | null;
}
interface Page { results: Upload[]; count: number; }
const active = new Set(["PENDING", "QUEUED", "PROCESSING"]);
const inputStyle = "w-full rounded-xl border border-black/15 bg-white/50 px-4 py-3 text-sm dark:border-white/15 dark:bg-white/5";

export default function PrescriptionReader() {
  const { user } = useAuth();
  const isDoctor = user?.role === "doctor";
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState("");
  const [mode, setMode] = useState("printed");
  const [consent, setConsent] = useState(false);
  const [history, setHistory] = useState<Upload[]>([]);
  const [count, setCount] = useState(0);
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  const [selected, setSelected] = useState<Upload | null>(null);
  const [correction, setCorrection] = useState("");
  const [review, setReview] = useState("");
  const [busy, setBusy] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const fileInput = useRef<HTMLInputElement>(null);

  async function loadHistory(current = page, query = search) {
    try {
      const { data } = await api.get<Page>("/prescription-reader/", { params: { page: current, search: query } });
      setHistory(data.results); setCount(data.count);
    } catch (err) { setError(getApiErrorMessage(err)); }
    finally { setLoading(false); }
  }
  async function selectUpload(id: string) {
    try {
      const { data } = await api.get<Upload>(`/prescription-reader/${id}/`);
      setSelected(data); setCorrection(data.personal_correction?.text || data.result.transcription || "");
    } catch (err) { setError(getApiErrorMessage(err)); }
  }
  useEffect(() => { if (user) void loadHistory(page); }, [page, user]); // eslint-disable-line react-hooks/exhaustive-deps
  useEffect(() => {
    if (!file) { setPreview(""); return; }
    const url = URL.createObjectURL(file); setPreview(url);
    return () => URL.revokeObjectURL(url);
  }, [file]);
  useEffect(() => {
    if (!selected || !active.has(selected.status)) return;
    const timer = setInterval(() => { void selectUpload(selected.id); void loadHistory(); }, 3000);
    return () => clearInterval(timer);
  }, [selected?.id, selected?.status]); // eslint-disable-line react-hooks/exhaustive-deps

  function pickFile(candidate?: File) {
    setError(""); setNotice("");
    if (!candidate) return;
    if (!/\.(png|jpe?g|pdf)$/i.test(candidate.name) || !candidate.size || candidate.size > 10 * 1024 * 1024) {
      setError("Choose a nonempty JPG, PNG, or PDF up to 10 MB. PDFs may contain at most 5 pages."); return;
    }
    setFile(candidate);
  }
  async function upload(e: React.FormEvent) {
    e.preventDefault(); if (!file) return;
    setBusy(true); setError(""); setNotice("");
    const form = new FormData(); form.append("file", file); form.append("recognition_mode", mode);
    form.append("external_consent", String(consent));
    try {
      const { data } = await api.post<Upload>("/prescription-reader/", form);
      setSelected(data); setFile(null); setCorrection(""); setPage(1); await loadHistory(1);
      setNotice("Original saved privately. Processing status updates automatically; pending jobs wait for the worker.");
    } catch (err) { setError(getApiErrorMessage(err)); }
    finally { setBusy(false); }
  }
  async function action(path: string, payload: object = {}) {
    if (!selected) return;
    setBusy(true); setError(""); setNotice("");
    try {
      await api.post(`/prescription-reader/${selected.id}/${path}/`, payload);
      await selectUpload(selected.id); await loadHistory(); setNotice("Saved."); setReview("");
    } catch (err) { setError(getApiErrorMessage(err)); }
    finally { setBusy(false); }
  }
  async function download() {
    if (!selected) return;
    try {
      const { data } = await api.get<Blob>(`/prescription-reader/${selected.id}/download/`, { responseType: "blob" });
      const url = URL.createObjectURL(data); const link = document.createElement("a");
      link.href = url; link.download = "prescription-transcription.txt"; link.click();
      setTimeout(() => URL.revokeObjectURL(url), 1000);
    } catch (err) { setError(getApiErrorMessage(err)); }
  }

  return <DashboardShell>
    <div className="mb-6"><p className="text-xs font-semibold uppercase tracking-widest text-[var(--color-primary)]">Your prescription, more readable</p>
      <h1 className="mt-2 font-display text-2xl font-bold">AI Prescription Reader</h1>
      <p className="mt-2 text-sm text-[var(--color-text-muted)]">{isDoctor ? "Review original documents shared by patients in your clinical workflow." : "Upload a prescription and compare the transcription with its original."}</p></div>
    {error && <div role="alert" className="mb-4 rounded-xl bg-red-500/10 p-4 text-sm text-red-700 dark:text-red-300">{error}</div>}
    {notice && <p role="status" className="mb-4 rounded-xl bg-teal-500/10 p-4 text-sm">{notice}</p>}
    <div className="mb-6 flex items-start gap-3 rounded-xl border border-amber-500/30 bg-amber-500/10 p-4 text-sm">
      <AlertTriangle size={20} className="shrink-0" /><p>This is an unverified transcription, not medical advice. Unclear medicines or doses must be checked against the original by a licensed clinician or pharmacist. Missing information is never filled in.</p></div>
    {!isDoctor && <GlassCard hover={false} className="mb-6">
      <form onSubmit={upload} className="space-y-4">
        <button type="button" onClick={() => fileInput.current?.click()} onDragOver={(e) => e.preventDefault()}
          onDrop={(e) => { e.preventDefault(); pickFile(e.dataTransfer.files[0]); }}
          className="flex w-full flex-col items-center gap-2 rounded-2xl border-2 border-dashed border-teal-500/40 bg-teal-500/5 px-6 py-8 text-center focus-visible:outline-2 focus-visible:outline-teal-600">
          <UploadCloud className="text-teal-600" size={32} /><span className="font-semibold">{file?.name || "Drop a prescription here, or choose a file"}</span>
          <span className="text-xs text-[var(--color-text-muted)]">JPG, PNG, or PDF · Up to 10 MB · Up to 5 PDF pages</span></button>
        <input ref={fileInput} type="file" accept=".jpg,.jpeg,.png,.pdf" aria-label="Prescription file" className="sr-only" onChange={(e) => pickFile(e.target.files?.[0])} />
        {preview && (file?.name.toLowerCase().endsWith(".pdf") ? <iframe title="Selected prescription PDF" src={preview} className="h-64 w-full rounded-xl border" /> : <img src={preview} alt="Selected prescription preview" className="max-h-64 rounded-xl object-contain" />)}
        <label className="block text-sm font-medium">Writing type<select className={`${inputStyle} mt-2`} value={mode} onChange={(e) => setMode(e.target.value)}>
          <option value="printed">Printed text — local OCR</option><option value="handwritten">Handwriting — configured vision model required</option></select></label>
        {mode === "handwritten" && <div className="space-y-2 rounded-xl bg-black/5 p-4 text-sm dark:bg-white/5">
          <p>Handwriting requires an operator-configured vision model. If it is unavailable, the file is preserved and the service status is shown.</p>
          <label className="flex items-start gap-3"><input type="checkbox" checked={consent} onChange={(e) => setConsent(e.target.checked)} className="mt-1" />
            <span>I authorize sending this document to the configured external vision provider if the hospital has enabled it. Local OCR does not require this consent.</span></label></div>}
        <Button type="submit" disabled={!file || busy} loading={busy}><UploadCloud size={16} /> Save and transcribe</Button>
      </form></GlassCard>}
    <div className="grid gap-6 xl:grid-cols-[300px_1fr]">
      <GlassCard hover={false}>
        <h2 className="mb-4 font-display font-semibold">{isDoctor ? "Requested reviews" : "Transcription history"}</h2>
        <form onSubmit={(e) => { e.preventDefault(); setPage(1); void loadHistory(1); }} className="mb-4 flex gap-2">
          <input aria-label="Search prescriptions" value={search} onChange={(e) => setSearch(e.target.value)} className={inputStyle} placeholder="Search filename" /><Button type="submit" variant="secondary">Search</Button></form>
        {loading ? <p role="status" className="text-sm">Loading prescriptions…</p> : !history.length ? <p className="text-sm text-[var(--color-text-muted)]">{isDoctor ? "No review requests from your assigned patients." : "No prescriptions uploaded yet."}</p> : <ul className="space-y-2">{history.map((item) => <li key={item.id}>
          <button onClick={() => void selectUpload(item.id)} aria-pressed={item.id === selected?.id} className={`w-full rounded-xl border p-3 text-left text-sm ${item.id === selected?.id ? "border-teal-500 bg-teal-500/10" : "border-black/10 dark:border-white/10"}`}>
            <span className="flex gap-2 font-medium"><FileText size={16} className="shrink-0" /><span className="break-all">{item.original_filename}</span></span>
            {isDoctor && <span className="mt-1 block">{item.patient_name}</span>}<span className="mt-2 block text-xs">{item.status.replaceAll("_", " ")} · {new Date(item.created_at).toLocaleDateString()}</span>
          </button></li>)}</ul>}
        <div className="mt-4 flex items-center justify-between gap-2 text-xs"><Button variant="ghost" disabled={page === 1} onClick={() => setPage((n) => n - 1)}>Previous</Button><span>Page {page}</span><Button variant="ghost" disabled={page * 20 >= count} onClick={() => setPage((n) => n + 1)}>Next</Button></div>
      </GlassCard>
      <GlassCard hover={false}>
        {!selected ? <div className="py-16 text-center text-sm text-[var(--color-text-muted)]"><FileText className="mx-auto mb-4" size={36} />Select a prescription to view its original and transcription.</div> : <div className="space-y-5">
          <div className="flex flex-wrap items-center justify-between gap-3"><div><h2 className="font-semibold break-all">{selected.original_filename}</h2><p role="status" className="mt-1 text-sm">{selected.status === "PENDING" ? "Waiting for the processing worker" : selected.status.replaceAll("_", " ")}</p></div>
            <Button variant="ghost" onClick={() => void selectUpload(selected.id)}><RefreshCw size={15} /> Refresh original link</Button></div>
          {selected.file_url && (selected.mime_type === "application/pdf" ? <iframe title="Original prescription" src={selected.file_url} className="h-80 w-full rounded-xl border" /> : <img src={selected.file_url} alt="Original uploaded prescription" className="max-h-96 w-full rounded-xl object-contain" />)}
          {active.has(selected.status) && <p className="animate-pulse text-sm text-teal-700 dark:text-teal-300">Processing status refreshes every three seconds. The original document is preserved.</p>}
          {selected.error_message && <div role="alert" className="rounded-xl bg-amber-500/10 p-4 text-sm">{selected.error_message}</div>}
          {!isDoctor && ["FAILED", "UNAVAILABLE"].includes(selected.status) && <Button loading={busy} onClick={() => void action("retry")}>Retry processing</Button>}
          {selected.status === "COMPLETED" && <>
            <div><h3 className="font-semibold">Original machine transcription</h3><p className="mt-1 text-xs text-amber-700 dark:text-amber-300">{selected.result.readability === "unreadable" ? "Not readable — no text could be reliably extracted." : "Unverified — compare every medicine and dose with the original."}</p>
              <pre className="mt-3 whitespace-pre-wrap break-words rounded-xl bg-black/5 p-4 text-sm dark:bg-white/5">{selected.result.transcription || "[Not readable]"}</pre></div>
            <div className="flex flex-wrap gap-2"><Button variant="secondary" disabled={!selected.result.transcription} onClick={() => { void navigator.clipboard.writeText(selected.result.transcription || "").then(() => setNotice("Transcription copied.")).catch(() => setError("Clipboard access failed. Select and copy the displayed text.")); }}><Copy size={15} /> Copy</Button><Button variant="secondary" onClick={() => void download()}><Download size={15} /> Download text</Button></div>
            <div className="overflow-x-auto"><h3 className="mb-3 font-semibold">Structured information</h3><table className="w-full text-left text-sm"><thead><tr className="border-b border-black/10 dark:border-white/10"><th className="py-2 pr-3">Field</th><th className="py-2 pr-3">Extracted content</th><th className="py-2">Status</th></tr></thead><tbody>{selected.result.fields?.map((field, i) => <tr key={`${field.field}-${i}`} className="border-b border-black/5 dark:border-white/5"><td className="py-3 pr-3 capitalize">{field.field.replaceAll("_", " ")}</td><td className="py-3 pr-3 break-words">{field.value || (field.status === "not_present" ? "Not present" : "Not readable")}{field.page && <span className="ml-2 text-xs text-[var(--color-text-muted)]">p. {field.page}</span>}</td><td className="py-3 text-xs text-amber-700 dark:text-amber-300">{field.status.replaceAll("_", " ")}</td></tr>)}</tbody></table><p className="mt-3 text-xs text-[var(--color-text-muted)]">Only explicit labels are extracted. Unlabelled fields remain absent. Recognition confidence is not clinically calibrated.</p></div>
            {!isDoctor && <form onSubmit={(e) => { e.preventDefault(); void action("correction", { text: correction }); }} className="space-y-3"><label className="block text-sm font-semibold">Personal readability correction<textarea className={`${inputStyle} mt-2`} rows={5} value={correction} maxLength={40000} onChange={(e) => setCorrection(e.target.value)} /></label><p className="text-xs text-[var(--color-text-muted)]">Saved separately with history. Does not alter the original, machine transcription, or clinical record.</p><Button type="submit" variant="secondary" loading={busy} disabled={!correction.trim()}>Save personal correction</Button></form>}
          </>}
          {!isDoctor && <Button variant="secondary" disabled={!!selected.review_requested_at || busy} onClick={() => void action("request-review")}>{selected.review_requested_at ? "Review requested from treating doctor" : "Request treating-doctor review"}</Button>}
          {isDoctor && <form onSubmit={(e) => { e.preventDefault(); void action("review", { notes: review }); }} className="space-y-3"><label className="block text-sm font-semibold">Clinical review notes<textarea className={`${inputStyle} mt-2`} value={review} onChange={(e) => setReview(e.target.value)} required maxLength={10000} rows={4} /></label><Button type="submit" loading={busy}>Record review</Button></form>}
          {!!selected.reviews.length && <div><h3 className="mb-3 font-semibold">Clinical review history</h3>{selected.reviews.map((item) => <div key={item.id} className="mb-2 rounded-xl bg-teal-500/10 p-4 text-sm"><p className="font-semibold">Dr. {item.doctor_name} · {new Date(item.created_at).toLocaleString()}</p><p className="mt-2 whitespace-pre-wrap">{item.notes}</p></div>)}</div>}
        </div>}
      </GlassCard>
    </div>
  </DashboardShell>;
}
