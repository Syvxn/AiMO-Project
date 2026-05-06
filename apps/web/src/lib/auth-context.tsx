"use client";

/* eslint-disable react-hooks/set-state-in-effect */

import React, { createContext, useContext, useState, useEffect } from "react";

type Role = "admin" | "teacher" | "student";

function toRole(value: string | null): Role | null {
  if (value === "admin" || value === "teacher" || value === "student") {
    return value;
  }
  return null;
}

interface AuthContextType {
  token: string | null;
  email: string | null;
  role: Role | null;
  isLoading: boolean;
  login: (token: string, email: string, role: Role) => void;
  logout: () => void;
  isAuthenticated: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [token, setToken] = useState<string | null>(null);
  const [email, setEmail] = useState<string | null>(null);
  const [role, setRole] = useState<Role | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    // Load token from localStorage on mount
    const savedToken = localStorage.getItem("token");
    const savedEmail = localStorage.getItem("email");
    const savedRole = localStorage.getItem("role");

    if (savedToken) {
      setToken(savedToken);
      setEmail(savedEmail);
      setRole(toRole(savedRole));
    }
    setIsLoading(false);
  }, []);

  const login = (newToken: string, newEmail: string, newRole: Role) => {
    setToken(newToken);
    setEmail(newEmail);
    setRole(newRole);
    localStorage.setItem("token", newToken);
    localStorage.setItem("email", newEmail);
    localStorage.setItem("role", newRole);
  };

  const logout = () => {
    setToken(null);
    setEmail(null);
    setRole(null);
    localStorage.removeItem("token");
    localStorage.removeItem("email");
    localStorage.removeItem("role");
  };

  return (
    <AuthContext.Provider
      value={{
        token,
        email,
        role,
        isLoading,
        login,
        logout,
        isAuthenticated: !!token,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error("useAuth must be used within AuthProvider");
  }
  return context;
}
