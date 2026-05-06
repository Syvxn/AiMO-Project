export default function AboutPage() {
  return (
    <section className="space-y-6">
      <h1 className="font-display text-4xl">About AiMO</h1>
      <div className="card space-y-4 max-w-4xl">
        <p>
          AiMO is an educational platform that merges multiplayer gameplay, teacher
          analytics, and AI-generated quizzes into one feedback loop.
        </p>
        <p>
          The long-term architecture connects a Godot-based world, a FastAPI backend,
          and agent tools for quiz generation and classroom insights.
        </p>
      </div>
    </section>
  );
}
