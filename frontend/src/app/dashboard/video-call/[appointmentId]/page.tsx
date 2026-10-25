"use client";

import { useEffect, useRef, useState, useCallback } from "react";
import { useParams, useRouter } from "next/navigation";
import { Mic, MicOff, Video, VideoOff, PhoneOff, Loader2 } from "lucide-react";
import { getWsUrl } from "@/lib/ws";
import { useAuth } from "@/context/AuthContext";
import DashboardShell from "@/components/DashboardShell";
import GlassCard from "@/components/GlassCard";
import Badge from "@/components/Badge";

// Public STUN server only — no TURN server configured, so this works
// reliably on the same network / most direct connections, but may fail
// across some restrictive NATs. Good enough for a demo; add a TURN server
// (e.g. Twilio NTS, coturn) for production reliability.
const ICE_SERVERS = [{ urls: "stun:stun.l.google.com:19302" }];

type CallStatus = "connecting" | "waiting" | "connected" | "ended" | "error";

export default function VideoCallPage() {
  const { appointmentId } = useParams<{ appointmentId: string }>();
  const router = useRouter();
  const { user } = useAuth();

  const localVideoRef = useRef<HTMLVideoElement>(null);
  const remoteVideoRef = useRef<HTMLVideoElement>(null);
  const pcRef = useRef<RTCPeerConnection | null>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const localStreamRef = useRef<MediaStream | null>(null);
  const makingOfferRef = useRef(false);

  const [status, setStatus] = useState<CallStatus>("connecting");
  const [micOn, setMicOn] = useState(true);
  const [camOn, setCamOn] = useState(true);
  const [errorMsg, setErrorMsg] = useState("");

  const cleanup = useCallback(() => {
    localStreamRef.current?.getTracks().forEach((t) => t.stop());
    pcRef.current?.close();
    wsRef.current?.close();
  }, []);

  useEffect(() => {
    let cancelled = false;

    async function start() {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: true });
        if (cancelled) return;
        localStreamRef.current = stream;
        if (localVideoRef.current) localVideoRef.current.srcObject = stream;

        const pc = new RTCPeerConnection({ iceServers: ICE_SERVERS });
        pcRef.current = pc;
        stream.getTracks().forEach((track) => pc.addTrack(track, stream));

        pc.ontrack = (event) => {
          if (remoteVideoRef.current) remoteVideoRef.current.srcObject = event.streams[0];
          setStatus("connected");
        };

        const ws = new WebSocket(getWsUrl(`/ws/video-call/${appointmentId}/`));
        wsRef.current = ws;

        pc.onicecandidate = (event) => {
          if (event.candidate && ws.readyState === WebSocket.OPEN) {
            ws.send(JSON.stringify({ type: "ice-candidate", candidate: event.candidate }));
          }
        };

        pc.onnegotiationneeded = async () => {
          try {
            makingOfferRef.current = true;
            const offer = await pc.createOffer();
            await pc.setLocalDescription(offer);
            ws.send(JSON.stringify({ type: "offer", sdp: pc.localDescription }));
          } finally {
            makingOfferRef.current = false;
          }
        };

        ws.onopen = () => setStatus("waiting");

        ws.onmessage = async (event) => {
          const msg = JSON.parse(event.data);

          if (msg.type === "peer_joined") {
            setStatus((s) => (s === "connected" ? s : "waiting"));
          } else if (msg.type === "peer_left") {
            setStatus("waiting");
            if (remoteVideoRef.current) remoteVideoRef.current.srcObject = null;
          } else if (msg.type === "offer") {
            await pc.setRemoteDescription(new RTCSessionDescription(msg.sdp));
            const answer = await pc.createAnswer();
            await pc.setLocalDescription(answer);
            ws.send(JSON.stringify({ type: "answer", sdp: pc.localDescription }));
          } else if (msg.type === "answer") {
            await pc.setRemoteDescription(new RTCSessionDescription(msg.sdp));
          } else if (msg.type === "ice-candidate" && msg.candidate) {
            try {
              await pc.addIceCandidate(new RTCIceCandidate(msg.candidate));
            } catch {
              // benign if it arrives before remote description is set
            }
          }
        };

        ws.onerror = () => setStatus("error");
        ws.onclose = () => setStatus((s) => (s === "connected" ? "ended" : s));
      } catch (err) {
        setErrorMsg(err instanceof Error ? err.message : "Couldn't access camera/microphone.");
        setStatus("error");
      }
    }

    start();
    return () => {
      cancelled = true;
      cleanup();
    };
  }, [appointmentId, cleanup]);

  function toggleMic() {
    const track = localStreamRef.current?.getAudioTracks()[0];
    if (track) {
      track.enabled = !track.enabled;
      setMicOn(track.enabled);
    }
  }

  function toggleCam() {
    const track = localStreamRef.current?.getVideoTracks()[0];
    if (track) {
      track.enabled = !track.enabled;
      setCamOn(track.enabled);
    }
  }

  function endCall() {
    cleanup();
    setStatus("ended");
    router.back();
  }

  const statusLabel: Record<CallStatus, string> = {
    connecting: "Setting up your camera...",
    waiting: "Waiting for the other participant to join...",
    connected: "Connected",
    ended: "Call ended",
    error: errorMsg || "Something went wrong",
  };

  return (
    <DashboardShell>
      <div className="mx-auto max-w-4xl">
        <div className="mb-4 flex items-center justify-between">
          <h1 className="font-display text-xl font-bold">Video Consultation</h1>
          <Badge tone={status === "connected" ? "vital" : status === "error" ? "alert" : "warn"}>
            {statusLabel[status]}
          </Badge>
        </div>

        <GlassCard hover={false} className="relative overflow-hidden !p-0">
          <div className="relative aspect-video w-full bg-black">
            <video ref={remoteVideoRef} autoPlay playsInline className="h-full w-full object-cover" />
            {status !== "connected" && (
              <div className="absolute inset-0 flex flex-col items-center justify-center gap-3 text-white/70">
                <Loader2 className="animate-spin" size={32} />
                <p className="text-sm">{statusLabel[status]}</p>
              </div>
            )}
            <video
              ref={localVideoRef}
              autoPlay
              playsInline
              muted
              className="absolute bottom-4 right-4 h-32 w-48 rounded-xl border-2 border-white/20 object-cover shadow-lg"
            />
          </div>

          <div className="flex items-center justify-center gap-4 p-5">
            <button
              onClick={toggleMic}
              className={`flex h-12 w-12 items-center justify-center rounded-full ${micOn ? "glass" : "bg-red-500 text-white"}`}
            >
              {micOn ? <Mic size={18} /> : <MicOff size={18} />}
            </button>
            <button onClick={endCall} className="flex h-14 w-14 items-center justify-center rounded-full bg-[var(--color-alert)] text-white">
              <PhoneOff size={20} />
            </button>
            <button
              onClick={toggleCam}
              className={`flex h-12 w-12 items-center justify-center rounded-full ${camOn ? "glass" : "bg-red-500 text-white"}`}
            >
              {camOn ? <Video size={18} /> : <VideoOff size={18} />}
            </button>
          </div>
        </GlassCard>

        <p className="mt-4 text-center text-xs text-[var(--color-text-muted)]">
          Signed in as {user?.first_name} · Appointment {appointmentId}
        </p>
      </div>
    </DashboardShell>
  );
}
