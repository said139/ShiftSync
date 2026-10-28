import React, { createContext, useContext, useEffect, useState } from "react";
import { apiClient, setAccessToken } from "../api/client";

export type UserRole =
  | "OUTGOING_WORKER"
  | "INCOMING_WORKER"
  | "SUPERVISOR"
  | "ADMIN";

export interface UserProfile {
  id: string;
  email: string;
  full_name: string;
  employee_id: string;
  role: UserRole;
  role_display: string;
  organisation: string;
  organisation_name: string;
  organisation_code: string;
  department: string;
  phone_number: string;
  is_active: boolean;
}

export interface OrganisationConfig {
  id: string;
  name: string;
  code: string;
  industry: string;
  departments: string[];
  task_categories: string[];
  priority_levels: string[];
  require_acknowledgment_notes: boolean;
  low_confidence_threshold: number;
  nlp_enabled: boolean;
}

interface AuthContextValue {
  user: UserProfile | null;
  organisation: OrganisationConfig | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<UserProfile>;
  register: (payload: Record<string, any>) => Promise<{ user: UserProfile; requires_approval: boolean; detail?: string }>;
  logout: () => Promise<void>;
  refreshProfile: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({
  children,
}) => {
  const [user, setUser] = useState<UserProfile | null>(null);
  const [organisation, setOrganisation] = useState<OrganisationConfig | null>(
    null
  );
  const [loading, setLoading] = useState<boolean>(true);

  const restoreSession = async () => {
    try {
      const res = await apiClient.post("/auth/refresh/", {});
      if (res.data?.access) {
        setAccessToken(res.data.access);
        setUser(res.data.user);
        setOrganisation(res.data.organisation);
      }
    } catch {
      setAccessToken(null);
      setUser(null);
      setOrganisation(null);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    restoreSession();
  }, []);

  const login = async (
    email: string,
    password: string
  ): Promise<UserProfile> => {
    const res = await apiClient.post("/auth/login/", { email, password });
    setAccessToken(res.data.access);
    setUser(res.data.user);
    setOrganisation(res.data.organisation);
    return res.data.user;
  };

  const register = async (
    payload: Record<string, any>
  ): Promise<{ user: UserProfile; requires_approval: boolean; detail?: string }> => {
    const res = await apiClient.post("/auth/register/", payload);
    if (res.data.access) {
      setAccessToken(res.data.access);
      setUser(res.data.user);
      if (res.data.organisation) {
        setOrganisation(res.data.organisation);
      }
    }
    return {
      user: res.data.user,
      requires_approval: Boolean(res.data.requires_approval),
      detail: res.data.detail,
    };
  };

  const logout = async () => {
    try {
      await apiClient.post("/auth/logout/", {});
    } catch {
      // Ignore network errors on logout
    } finally {
      setAccessToken(null);
      setUser(null);
      setOrganisation(null);
    }
  };

  const refreshProfile = async () => {
    const res = await apiClient.get("/auth/me/");
    setUser(res.data.user);
    setOrganisation(res.data.organisation);
  };

  return (
    <AuthContext.Provider
      value={{ user, organisation, loading, login, register, logout, refreshProfile }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error("useAuth must be used inside an AuthProvider");
  }
  return ctx;
}
