"use client";

import { createContext, useContext, useEffect, useState, ReactNode } from "react";
import { useRouter } from "next/navigation";
import api, { getApiErrorMessage, setAccessToken, refreshAccessToken } from "@/lib/api";

export type Role = "patient" | "doctor" | "hospital_admin" | "laboratory" | "pharmacy";

export interface AuthUser {
  id: string;
  username: string;
  email: string;
  role: Role;
  first_name: string;
  last_name: string;
  phone_number?: string;
  is_email_verified?: boolean;
  is_2fa_enabled?: boolean;
}

interface AuthContextValue {
  user: AuthUser | null;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<{ requires2fa: boolean; challenge?: string }>;
  verify2fa: (challenge: string, code: string) => Promise<void>;
  register: (payload: Record<string, unknown>) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export const ROLE_DASHBOARD_PATH: Record<Role, string> = {
  patient: "/dashboard/patient",
  doctor: "/dashboard/doctor",
  hospital_admin: "/dashboard/hospital-admin",
  laboratory: "/dashboard/laboratory",
  pharmacy: "/dashboard/pharmacy",
};

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const router = useRouter();

  useEffect(() => {
    let active = true;
    // Remove credentials from earlier versions of the application.
    ["access_token", "refresh_token", "user"].forEach((key) => localStorage.removeItem(key));
    refreshAccessToken().then(() => api.get<AuthUser>("/auth/me/"))
      .then(({ data }) => { if (active) setUser(data); })
      .catch(() => { if (active) setUser(null); })
      .finally(() => { if (active) setIsLoading(false); });
    return () => { active = false; };
  }, []);

  async function login(email: string, password: string) {
    try {
      const { data } = await api.post("/auth/token/", { email, password });

      if (data.requires_2fa) {
        return { requires2fa: true, challenge: data.challenge };
      }

      setAccessToken(data.access);
      setUser(data.user);
      router.push(ROLE_DASHBOARD_PATH[data.user.role as Role] || "/dashboard/patient");
      return { requires2fa: false };
    } catch (error) {
      throw new Error(getApiErrorMessage(error));
    }
  }

  async function verify2fa(challenge: string, code: string) {
    try {
      const { data } = await api.post("/auth/2fa/login-verify/", { challenge, code });
      setAccessToken(data.access);
      setUser(data.user);
      router.push(ROLE_DASHBOARD_PATH[data.user.role as Role] || "/dashboard/patient");
    } catch (error) {
      throw new Error(getApiErrorMessage(error));
    }
  }

  async function register(payload: Record<string, unknown>) {
    try {
      await api.post("/auth/register/", payload);
    } catch (error) {
      throw new Error(getApiErrorMessage(error));
    }
  }

  function logout() {
    void api.post("/auth/logout/").then(() => {
      setAccessToken(null);
      setUser(null);
      router.push("/login");
    }).catch(() => {
      window.alert("Sign-out could not reach the server. Please retry to revoke this session.");
    });
  }

  return (
    <AuthContext.Provider value={{ user, isLoading, login, verify2fa, register, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
