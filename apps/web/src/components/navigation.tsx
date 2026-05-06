'use client';

import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/lib/auth-context';

export function Navigation() {
  const { isAuthenticated, email, role, logout } = useAuth();
  const router = useRouter();

  const handleLogout = () => {
    logout();
    router.push('/');
  };

  return (
    <nav className="mx-auto flex w-full max-w-6xl items-center justify-between px-6 py-4">
      <Link href="/" className="font-display text-2xl tracking-tight">
        AiMO
      </Link>
      <div className="flex items-center gap-4 text-sm sm:gap-6">
        <Link href="/play">Play</Link>
        <Link href="/about">About</Link>
        <Link href="/contact">Contact</Link>
        {role === 'admin' && <Link href="/admin">Admin</Link>}
        
        {isAuthenticated ? (
          <div className="flex items-center gap-3 pl-4 border-l border-white/20">
            <span className="text-xs text-slate-300">{email}</span>
            <button
              onClick={handleLogout}
              className="text-xs px-3 py-1 rounded-full bg-red-600/20 text-red-300 hover:bg-red-600/30"
            >
              Logout
            </button>
          </div>
        ) : (
          <>
            <Link href="/login">Login</Link>
            <Link className="btn-primary text-xs" href="/register">Register</Link>
          </>
        )}
      </div>
    </nav>
  );
}
