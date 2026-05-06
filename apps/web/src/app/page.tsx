import Link from "next/link";

export default function Home() {
  return (
    <section className="flex flex-1 flex-col justify-center gap-6 py-4 xl:gap-8 xl:py-6">
      <div className="grid gap-6 rounded-[2rem] border border-accent-orange/40 bg-gradient-to-br from-bg-dark/50 to-bg-medium/35 p-6 shadow-2xl backdrop-blur md:p-8 xl:grid-cols-[1.35fr_1fr] xl:gap-8 xl:p-10 min-[2200px]:min-h-[36rem] min-[2200px]:gap-10 min-[2200px]:p-12">
        <div className="flex flex-col justify-between gap-8">
          <div className="space-y-6 xl:space-y-7">
            <p className="font-display text-sm uppercase tracking-[0.3em] text-accent-yellow xl:text-[0.95rem]">
              Learn through play
            </p>
            <h1 className="font-display text-4xl leading-tight text-text-natural sm:text-5xl xl:max-w-3xl xl:text-[3rem] min-[2200px]:max-w-4xl min-[2200px]:text-[3.6rem]">
              Multiplayer game learning powered by AI quiz agents
            </h1>
            <p className="max-w-2xl text-lg text-text-beige xl:text-[1.15rem] xl:leading-8">
              AiMO combines a Godot multiplayer world with agent-generated quizzes for students,
              teachers, and administrators in one connected platform.
            </p>
            <div className="flex flex-wrap gap-3 xl:gap-4">
              <Link className="btn-primary xl:px-6 xl:py-3 xl:text-[0.95rem]" href="/play">
                Start Playing
              </Link>
              <Link className="btn-secondary xl:px-6 xl:py-3 xl:text-[0.95rem]" href="/register">
                Create Account
              </Link>
            </div>
          </div>
          <div className="grid gap-4 md:grid-cols-3 xl:gap-5">
            <article className="card bg-bg-darkest/55">
              <p className="font-display text-3xl text-accent-yellow xl:text-4xl">3</p>
              <p className="mt-2 text-sm uppercase tracking-[0.22em] text-text-beige">Roles</p>
              <p className="mt-3 text-sm leading-6 text-text-light/90">
                Admin, teacher, and student paths with separate access and tools.
              </p>
            </article>
            <article className="card bg-bg-darkest/55">
              <p className="font-display text-3xl text-accent-teal xl:text-4xl">Live</p>
              <p className="mt-2 text-sm uppercase tracking-[0.22em] text-text-beige">Stack</p>
              <p className="mt-3 text-sm leading-6 text-text-light/90">
                Next.js, FastAPI, PostgreSQL, and Nginx running together as one MVP.
              </p>
            </article>
            <article className="card bg-bg-darkest/55">
              <p className="font-display text-3xl text-accent-green xl:text-4xl">AI</p>
              <p className="mt-2 text-sm uppercase tracking-[0.22em] text-text-beige">Quiz Loop</p>
              <p className="mt-3 text-sm leading-6 text-text-light/90">
                Quiz generation, scoring, and classroom insights ready for agent integration.
              </p>
            </article>
          </div>
        </div>
        <div className="grid gap-5">
          <div className="rounded-2xl border border-accent-teal/30 bg-gradient-to-br from-bg-darkest/65 to-bg-dark/60 p-6 shadow-xl xl:p-8">
            <h2 className="font-display text-2xl text-text-natural xl:text-3xl">MVP Features</h2>
            <ul className="mt-5 list-disc space-y-3 pl-6 text-text-beige xl:text-lg">
              <li>Landing, About, Contact pages</li>
              <li>Login and Registration flows</li>
              <li>Playable web game entrypoint</li>
              <li>JWT auth with admin teacher student roles</li>
              <li>FastAPI quiz and score endpoints</li>
            </ul>
          </div>
        </div>
      </div>
    </section>
  );
}
