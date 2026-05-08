"use client";

import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth-context";
import { ReactNode, useEffect } from "react";

interface ProtectedRouteProps {
  children: ReactNode;
  requiredRole?: "admin" | "teacher" | "student";
  requiredRoles?: Array<"admin" | "teacher" | "student">;
}

export function ProtectedRoute({ children, requiredRole, requiredRoles }: ProtectedRouteProps) {
  const { isAuthenticated, role, isLoading } = useAuth();
  const router = useRouter();

  const hasRoleAccess =
    !requiredRole && !requiredRoles
      ? true
      : requiredRoles
        ? !!role && requiredRoles.includes(role)
        : role === requiredRole;

  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      router.push("/login");
    } else if (!isLoading && !hasRoleAccess) {
      router.push("/");
    }
  }, [isLoading, isAuthenticated, hasRoleAccess, router]);

  if (isLoading) {
    return <div className="flex items-center justify-center py-12">Loading...</div>;
  }

  if (!isAuthenticated) {
    return null;
  }

  if (!hasRoleAccess) {
    return <div className="text-red-400">Access denied.</div>;
  }

  return <>{children}</>;
}
