import axios, { AxiosError, InternalAxiosRequestConfig } from "axios";
import { withApiTrailingSlash } from "./api-path";

export const API_BASE_URL = (process.env.NEXT_PUBLIC_API_URL || "/api").replace(/\/+$/, "");
let accessToken: string | null = null;
let refreshPromise: Promise<string> | null = null;
export const getAccessToken = () => accessToken;
export const setAccessToken = (token: string | null) => { accessToken = token; };

function csrfToken(): string {
  if (typeof document === "undefined") return "";
  return document.cookie.split("; ").find((entry) => entry.startsWith("aihms_csrf="))?.split("=")[1] || "";
}

export async function refreshAccessToken(): Promise<string> {
  if (refreshPromise) return refreshPromise;
  const pending: Promise<string> = axios.post(withApiTrailingSlash(`${API_BASE_URL}/auth/token/refresh/`), {}, {
    withCredentials: true, headers: { "X-CSRFToken": csrfToken() },
  }).then(({ data }: { data: { access: string } }) => {
    accessToken = data.access;
    return data.access;
  }).finally(() => { refreshPromise = null; });
  refreshPromise = pending;
  return pending;
}

const api = axios.create({ baseURL: API_BASE_URL, withCredentials: true });
api.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  if (config.url) config.url = withApiTrailingSlash(config.url);
  if (accessToken) config.headers.Authorization = `Bearer ${accessToken}`;
  if (config.method !== "get") config.headers["X-CSRFToken"] = csrfToken();
  return config;
});
api.interceptors.response.use((response) => response, async (error: AxiosError) => {
  const original = error.config as (InternalAxiosRequestConfig & { _retry?: boolean }) | undefined;
  const authRequest = original?.url?.startsWith("/auth/");
  if (error.response?.status === 401 && original && !original._retry && !authRequest) {
    original._retry = true;
    try {
      const token = await refreshAccessToken();
      original.headers.Authorization = `Bearer ${token}`;
      return api(original);
    } catch {
      accessToken = null;
      if (typeof window !== "undefined") window.location.assign("/login");
    }
  }
  throw error;
});

export function getApiErrorMessage(error: unknown): string {
  if (axios.isAxiosError(error)) {
    const data = error.response?.data as { error?: { message?: string }; message?: string; detail?: string } | undefined;
    return data?.error?.message || data?.message || data?.detail || error.message || "Request failed.";
  }
  return error instanceof Error ? error.message : "Request failed.";
}
export default api;
