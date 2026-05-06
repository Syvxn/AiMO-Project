'use client';

import React, { createContext, useContext, useState, useEffect } from 'react';

interface AuthContextType {
  token: string | null;
  email: string | null;
  role: 'admin' | 'teacher' | 'student' | null;
  isLoading: boolean;
  login: (token: string, email: string, role: string) => void;
  logout: () => void;
  isAuthenticated: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [token, setToken] = useState<string | null>(null);
  const [email, setEmail] = useState<string | null>(null);
  const [role, setRole] = useState<'admin' | 'teacher' | 'student' | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    // Load token from localStorage on mount
    const savedToken = localStorage.getItem('token');
    const savedEmail = localStorage.getItem('email');
    const savedRole = localStorage.getItem('role');
    
    if (savedToken) {
      setToken(savedToken);
      setEmail(savedEmail);
      setRole(savedRole as any);
    }
    setIsLoading(false);
  }, []);

  const login = (newToken: string, newEmail: string, newRole: string) => {
    setToken(newToken);
    setEmail(newEmail);
    setRole(newRole as any);
    localStorage.setItem('token', newToken);
    localStorage.setItem('email', newEmail);
    localStorage.setItem('role', newRole);
  };

  const logout = () => {
    setToken(null);
    setEmail(null);
    setRole(null);
    localStorage.removeItem('token');
    localStorage.removeItem('email');
    localStorage.removeItem('role');
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
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
}
