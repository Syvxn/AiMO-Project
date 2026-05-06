import Link from "next/link";

export default function Home() {
  return (
    <section className="flex flex-1 flex-col gap-10 py-8">
      <div className="grid gap-8 rounded-2xl border border-accent-orange/40 bg-gradient-to-br from-bg-dark/40 to-bg-medium/30 p-8 shadow-2xl md:grid-cols-2 md:p-12 backdrop-blur">
        <div className="space-y-6">
          <p className="font-display text-sm uppercase tracking-[0.3em] text-accent-yellow">
            Learn through play
          </p>
          <h1 className="font-display text-4xl leading-tight sm:text-5xl text-text-natural">
            Multiplayer game learning powered by AI quiz agents
          </h1>
          <p className="max-w-xl text-lg text-text-beige">
            AiMO combines a Godot multiplayer world with agent-generated quizzes for
            students, teachers, and administrators in one connected platform.
          </p>
          <div className="flex flex-wrap gap-3">
            <Link className="btn-primary" href="/play">
              Start Playing
            </Link>
            <Link className="btn-secondary" href="/register">
              Create Account
            </Link>
          </div>
        </div>
        <div className="grid gap-4 rounded-xl border border-accent-teal/30 bg-gradient-to-br from-bg-darkest/50 to-transparent p-6">
          <h2 className="font-display text-2xl text-text-natural">MVP Features</h2>
          <ul className="list-disc space-y-2 pl-6 text-text-beige">
            <li>Landing, About, Contact pages</li>
            <li>Login and Registration flows</li>
            <li>Playable web game entrypoint</li>
            <li>JWT auth with admin teacher student roles</li>
            <li>FastAPI quiz and score endpoints</li>
          </ul>
        </div>
      </div>
    </section>
  );
}
