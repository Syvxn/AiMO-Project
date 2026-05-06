'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/lib/auth-context';
import { registerUser } from '@/lib/api';

export default function RegisterPage() {
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [role, setRole] = useState<'student' | 'teacher' | 'admin'>('student');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const { login } = useAuth();
  const router = useRouter();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setIsLoading(true);

    try {
      if (password.length < 8) {
        throw new Error('Password must be at least 8 characters');
      }
      const response = await registerUser(email, password, role);
      login(response.access_token, email, response.role);
      router.push('/play');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Registration failed');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <section className="space-y-6">
      <h1 className="font-display text-4xl">Register</h1>
      <form className="card max-w-xl space-y-4" onSubmit={handleSubmit}>
        {error && <div className="text-red-400 text-sm">{error}</div>}
        <div className="grid gap-4 sm:grid-cols-2">
          <div className="space-y-1">
            <label htmlFor="name" className="text-sm text-slate-300">
              Display Name
            </label>
            <input
              id="name"
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="w-full rounded-md border border-white/20 bg-slate-950/60 px-3 py-2"
            />
          </div>
          <div className="space-y-1">
            <label htmlFor="email" className="text-sm text-slate-300">
              Email
            </label>
            <input
              id="email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full rounded-md border border-white/20 bg-slate-950/60 px-3 py-2"
              required
            />
          </div>
        </div>
        <div className="space-y-1">
          <label htmlFor="password" className="text-sm text-slate-300">
            Password
          </label>
          <input
            id="password"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="w-full rounded-md border border-white/20 bg-slate-950/60 px-3 py-2"
            required
          />
          <p className="text-xs text-slate-400">Minimum 8 characters</p>
        </div>
        <div className="space-y-1">
          <label htmlFor="role" className="text-sm text-slate-300">
            Role
          </label>
          <select
            id="role"
            value={role}
            onChange={(e) => setRole(e.target.value as any)}
            className="w-full rounded-md border border-white/20 bg-slate-950/60 px-3 py-2"
          >
            <option value="student">Student</option>
            <option value="teacher">Teacher</option>
            <option value="admin">Admin</option>
          </select>
        </div>
        <button className="btn-primary w-full" type="submit" disabled={isLoading}>
          {isLoading ? 'Creating Account...' : 'Create Account'}
        </button>
        <p className="text-center text-sm text-slate-400">
          Already have an account?{' '}
          <a href="/login" className="text-amber-400 hover:underline">
            Login
          </a>
        </p>
      </form>
    </section>
  );
}
