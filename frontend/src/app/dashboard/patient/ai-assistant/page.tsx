"use client";

import { useState, useRef, useEffect } from "react";
import { Send, Sparkles, AlertTriangle } from "lucide-react";
import api from "@/lib/api";
import DashboardShell from "@/components/DashboardShell";
import GlassCard from "@/components/GlassCard";
import Badge from "@/components/Badge";

interface ChatMessage {
  role: "user" | "assistant";
  content: string;
}

const riskTone: Record<string, "vital" | "warn" | "alert"> = {
  LOW: "vital",
  MODERATE: "warn",
  HIGH: "alert",
  EMERGENCY: "alert",
};

export default function AiAssistantPage() {
  const [externalConsent, setExternalConsent] = useState(false);
  const [mode, setMode] = useState<"symptom" | "chat">("symptom");
  const [messages, setMessages] = useState<ChatMessage[]>([
    { role: "assistant", content: "Hi, I'm your AI health assistant. Describe what you're feeling and I'll ask a few follow-up questions before sharing guidance." },
  ]);
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([
    { role: "assistant", content: "Ask me anything about general wellness, nutrition, or health topics — I'm here to help explain things in plain language." },
  ]);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [input, setInput] = useState("");
  const [chatInput, setChatInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [chatLoading, setChatLoading] = useState(false);
  const [latestResult, setLatestResult] = useState<{ risk_level?: string; possible_conditions?: string[]; recommendation?: string } | null>(null);
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, chatMessages, mode]);

  async function handleChatSend(e: React.FormEvent) {
    e.preventDefault();
    if (!chatInput.trim()) return;
    const userMessage = chatInput.trim();
    setChatMessages((m) => [...m, { role: "user", content: userMessage }]);
    setChatInput("");
    setChatLoading(true);
    try {
      const { data } = await api.post("/ai/health-chat/", { message: userMessage }, { headers: { "X-AI-Consent": String(externalConsent) } });
      setChatMessages((m) => [...m, { role: "assistant", content: data.reply.content }]);
    } catch {
      setChatMessages((m) => [...m, { role: "assistant", content: "Sorry, something went wrong." }]);
    } finally {
      setChatLoading(false);
    }
  }

  async function handleSend(e: React.FormEvent) {
    e.preventDefault();
    if (!input.trim()) return;
    const userMessage = input.trim();
    setMessages((m) => [...m, { role: "user", content: userMessage }]);
    setInput("");
    setLoading(true);

    try {
      const endpoint = sessionId ? "/ai/symptom-check/reply/" : "/ai/symptom-check/start/";
      const payload = sessionId
        ? { session_id: sessionId, message: userMessage }
        : { initial_complaint: userMessage };
      const { data } = await api.post(endpoint, payload, { headers: { "X-AI-Consent": String(externalConsent) } });
      setSessionId(data.session_id);
      setLatestResult(data.result);

      const reply = data.result.need_followup
        ? data.result.followup_question
        : data.result.recommendation || "Thanks — here's my assessment on the right.";
      setMessages((m) => [...m, { role: "assistant", content: reply }]);
    } catch {
      setMessages((m) => [...m, { role: "assistant", content: "Sorry, something went wrong reaching the AI service." }]);
    } finally {
      setLoading(false);
    }
  }

  return (
    <DashboardShell>
      <label className="mb-6 flex items-start gap-3 rounded-xl border border-amber-500/30 bg-amber-500/10 p-4 text-sm"><input type="checkbox" checked={externalConsent} onChange={(e) => setExternalConsent(e.target.checked)} className="mt-1" /><span>I authorize sending information used by these AI requests to the hospital-configured external AI provider. These features remain unavailable unless the operator has configured and enabled a provider. This is not a diagnosis.</span></label>
      <div className="mb-4 flex gap-2">
        <button
          onClick={() => setMode("symptom")}
          className={`rounded-xl px-4 py-2 text-sm font-semibold transition-colors ${mode === "symptom" ? "bg-[var(--color-primary)] text-white" : "glass"}`}
        >
          Symptom Checker
        </button>
        <button
          onClick={() => setMode("chat")}
          className={`rounded-xl px-4 py-2 text-sm font-semibold transition-colors ${mode === "chat" ? "bg-[var(--color-primary)] text-white" : "glass"}`}
        >
          General Health Chat
        </button>
      </div>

      {mode === "chat" ? (
        <GlassCard hover={false} className="flex h-[560px] flex-col">
          <div className="mb-4 flex items-center gap-2">
            <Sparkles className="text-[var(--color-accent)]" size={18} />
            <h2 className="font-display font-semibold">AI Health Assistant</h2>
            <Badge tone="accent">General wellness Q&A</Badge>
          </div>
          <div className="flex-1 space-y-3 overflow-y-auto pr-1">
            {chatMessages.map((m, i) => (
              <div key={i} className={`flex ${m.role === "user" ? "justify-end" : "justify-start"}`}>
                <div className={`max-w-[75%] rounded-2xl px-4 py-2.5 text-sm ${m.role === "user" ? "bg-[var(--color-primary)] text-white" : "bg-black/[0.04] dark:bg-white/[0.06]"}`}>
                  {m.content}
                </div>
              </div>
            ))}
            {chatLoading && (
              <div className="flex justify-start">
                <div className="flex items-center gap-1 rounded-2xl bg-black/[0.04] px-4 py-3 dark:bg-white/[0.06]">
                  <span className="h-2 w-2 animate-bounce rounded-full bg-[var(--color-text-muted)] [animation-delay:-0.3s]" />
                  <span className="h-2 w-2 animate-bounce rounded-full bg-[var(--color-text-muted)] [animation-delay:-0.15s]" />
                  <span className="h-2 w-2 animate-bounce rounded-full bg-[var(--color-text-muted)]" />
                </div>
              </div>
            )}
            <div ref={endRef} />
          </div>
          <form onSubmit={handleChatSend} className="mt-4 flex gap-2">
            <input
              value={chatInput}
              onChange={(e) => setChatInput(e.target.value)}
              placeholder="Ask about nutrition, wellness, conditions..."
              className="flex-1 rounded-xl border border-black/10 bg-white/40 px-4 py-2.5 text-sm outline-none focus:border-[var(--color-primary)] dark:border-white/10 dark:bg-white/5"
            />
            <button type="submit" disabled={chatLoading} className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-[var(--color-primary)] text-white disabled:opacity-50">
              <Send size={18} />
            </button>
          </form>
        </GlassCard>
      ) : (
      <div className="grid gap-6 lg:grid-cols-3">
        <GlassCard hover={false} className="flex h-[560px] flex-col lg:col-span-2">
          <div className="mb-4 flex items-center gap-2">
            <Sparkles className="text-[var(--color-accent)]" size={18} />
            <h2 className="font-display font-semibold">AI Symptom Checker</h2>
            <Badge tone="accent">AI Generated — not a diagnosis</Badge>
          </div>
          <div className="flex-1 space-y-3 overflow-y-auto pr-1">
            {messages.map((m, i) => (
              <div key={i} className={`flex ${m.role === "user" ? "justify-end" : "justify-start"}`}>
                <div
                  className={`max-w-[75%] rounded-2xl px-4 py-2.5 text-sm ${
                    m.role === "user"
                      ? "bg-[var(--color-primary)] text-white"
                      : "bg-black/[0.04] dark:bg-white/[0.06]"
                  }`}
                >
                  {m.content}
                </div>
              </div>
            ))}
            {loading && (
              <div className="flex justify-start">
                <div className="flex items-center gap-1 rounded-2xl bg-black/[0.04] px-4 py-3 dark:bg-white/[0.06]">
                  <span className="h-2 w-2 animate-bounce rounded-full bg-[var(--color-text-muted)] [animation-delay:-0.3s]" />
                  <span className="h-2 w-2 animate-bounce rounded-full bg-[var(--color-text-muted)] [animation-delay:-0.15s]" />
                  <span className="h-2 w-2 animate-bounce rounded-full bg-[var(--color-text-muted)]" />
                </div>
              </div>
            )}
            <div ref={endRef} />
          </div>
          <form onSubmit={handleSend} className="mt-4 flex gap-2">
            <input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Describe your symptoms..."
              className="flex-1 rounded-xl border border-black/10 bg-white/40 px-4 py-2.5 text-sm outline-none focus:border-[var(--color-primary)] dark:border-white/10 dark:bg-white/5"
            />
            <button
              type="submit"
              disabled={loading}
              className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-[var(--color-primary)] text-white disabled:opacity-50"
            >
              <Send size={18} />
            </button>
          </form>
        </GlassCard>

        <GlassCard>
          <h3 className="mb-4 font-display font-semibold">Assessment</h3>
          {latestResult ? (
            <div className="space-y-4">
              {latestResult.risk_level && (
                <div>
                  <p className="text-xs text-[var(--color-text-muted)]">Risk level</p>
                  <Badge tone={riskTone[latestResult.risk_level] ?? "neutral"}>{latestResult.risk_level}</Badge>
                </div>
              )}
              {!!latestResult.possible_conditions?.length && (
                <div>
                  <p className="mb-1 text-xs text-[var(--color-text-muted)]">Possible considerations</p>
                  <ul className="list-inside list-disc text-sm">
                    {latestResult.possible_conditions.map((c) => <li key={c}>{c}</li>)}
                  </ul>
                </div>
              )}
              {latestResult.recommendation && (
                <div>
                  <p className="mb-1 text-xs text-[var(--color-text-muted)]">Recommendation</p>
                  <p className="text-sm">{latestResult.recommendation}</p>
                </div>
              )}
            </div>
          ) : (
            <p className="text-sm text-[var(--color-text-muted)]">Start chatting to see your assessment here.</p>
          )}
          <div className="mt-6 flex items-start gap-2 rounded-xl bg-amber-500/10 p-3 text-xs text-amber-700 dark:text-amber-400">
            <AlertTriangle size={16} className="mt-0.5 shrink-0" />
            This is an AI triage aid, not a medical diagnosis. For HIGH/EMERGENCY risk, contact a doctor or emergency services immediately.
          </div>
        </GlassCard>
      </div>
      )}
    </DashboardShell>
  );
}
