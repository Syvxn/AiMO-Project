'use client';

import { ProtectedRoute } from '@/components/protected-route';

function AdminContent() {
  return (
    <section className="space-y-6">
      <h1 className="font-display text-4xl text-text-natural">Admin Console</h1>
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        <article className="card">
          <h2 className="font-display text-xl text-text-natural">Users</h2>
          <p className="text-text-beige">Manage students, teachers, and admin roles.</p>
        </article>
        <article className="card">
          <h2 className="font-display text-xl text-text-natural">System Health</h2>
          <p className="text-text-beige">Monitor API, game services, and queue jobs.</p>
        </article>
        <article className="card">
          <h2 className="font-display text-xl text-text-natural">Content</h2>
          <p className="text-text-beige">Review learning materials and quiz pipelines.</p>
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
