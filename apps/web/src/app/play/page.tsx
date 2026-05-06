'use client';

import { ProtectedRoute } from '@/components/protected-route';

function PlayContent() {
  return (
    <section className="space-y-6">
      <h1 className="font-display text-4xl">Play</h1>
      <p className="max-w-3xl text-slate-200">
        This page will host the Godot web client and session bridge. For now, it acts
        as a launcher shell that will be connected to game and API health checks next.
      </p>

      <div className="card space-y-3">
        <h2 className="font-display text-2xl">Game Launcher</h2>
        <p className="text-slate-300">
          You are logged in and authenticated. The Godot game client will load here.
        </p>
        <button className="btn-primary" type="button">
          Launch Game (Stub)
        </button>
      </div>
    </section>
  );
}

export default function PlayPage() {
  return (
    <ProtectedRoute>
      <PlayContent />
    </ProtectedRoute>
  );
}
