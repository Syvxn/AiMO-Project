"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth-context";

export function Navigation() {
  const { isAuthenticated, email, role, logout } = useAuth();
  const router = useRouter();

  const handleLogout = () => {
    logout();
    router.push("/");
  };

  return (
    <nav className="mx-auto flex w-full max-w-6xl items-center justify-between px-4 py-4 sm:px-6 xl:max-w-7xl xl:px-8 min-[2200px]:max-w-[96rem] min-[2200px]:px-10">
      <Link
        href="/"
        className="font-display text-2xl tracking-tight text-text-natural xl:text-[1.75rem]"
      >
        AiMO
      </Link>
      <div className="flex items-center gap-4 text-sm sm:gap-6 xl:gap-8 xl:text-base">
        <Link href="/play" className="transition-colors hover:text-accent-orange">
          Play
        </Link>
        <Link href="/about" className="transition-colors hover:text-accent-orange">
          About
        </Link>
        <Link href="/contact" className="transition-colors hover:text-accent-orange">
          Contact
        </Link>
        {(role === "teacher" || role === "admin") && (
          <Link href="/teacher" className="transition-colors hover:text-accent-orange">
            Teacher
          </Link>
        )}
        {role === "admin" && (
          <Link href="/admin" className="transition-colors hover:text-accent-orange">
            Admin
          </Link>
        )}

        {isAuthenticated ? (
          <div className="flex items-center gap-3 pl-4 border-l border-accent-orange/30">
            <span className="text-xs text-text-beige">{email}</span>
            <button
              onClick={handleLogout}
              className="text-xs px-3 py-1 rounded-full bg-gradient-to-r from-accent-orange/30 to-accent-light/30 text-accent-light hover:from-accent-orange/50 hover:to-accent-light/50 transition-all"
            >
              Logout
            </button>
          </div>
        ) : (
          <>
            <Link href="/login" className="transition-colors hover:text-accent-orange">
              Login
            </Link>
            <Link className="btn-primary text-xs" href="/register">
              Register
            </Link>
          </>
        )}
      </div>
    </nav>
  );
}
