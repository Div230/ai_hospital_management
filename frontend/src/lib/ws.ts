import { getAccessToken } from "./api";
export function getWsUrl(path: string) {
  const wsBase = process.env.NEXT_PUBLIC_WS_URL || "ws://localhost:8000";
  return `${wsBase.replace(/\/$/, "")}${path}?token=${encodeURIComponent(getAccessToken() || "")}`;
}
