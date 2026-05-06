'use client';

import { ProtectedRoute } from '@/components/protected-route';

function AdminContent() {
  return (
    <section className="space-y-6">
      <h1 className="font-display text-4xl">Admin Console</h1>
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        <article className="card">
          <h2 className="font-display text-xl">Users</h2>
          <p className="text-slate-300">Manage students, teachers, and admin roles.</p>
        </article>
        <article className="card">
          <h2 className="font-display text-xl">System Health</h2>
          <p className="text-slate-300">Monitor API, game services, and queue jobs.</p>
        </article>
        <article className="card">
          <h2 className="font-display text-xl">Content</h2>
          <p className="text-slate-300">Review learning materials and quiz pipelines.</p>
        </article>
      </div>
    </section>
  );
}

export default function AdminPage() {
  return (
    <ProtectedRoute requiredRole="admin">
      <AdminContent />
    </ProtectedRoute>
  );
}
