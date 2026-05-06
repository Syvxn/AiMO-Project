export default function LoginPage() {
  return (
    <section className="space-y-6">
      <h1 className="font-display text-4xl">Login</h1>
      <form className="card max-w-md space-y-4">
        <div className="space-y-1">
          <label htmlFor="email" className="text-sm text-slate-300">Email</label>
          <input id="email" type="email" className="w-full rounded-md border border-white/20 bg-slate-950/60 px-3 py-2" />
        </div>
        <div className="space-y-1">
          <label htmlFor="password" className="text-sm text-slate-300">Password</label>
          <input id="password" type="password" className="w-full rounded-md border border-white/20 bg-slate-950/60 px-3 py-2" />
        </div>
        <button className="btn-primary" type="submit">Sign In</button>
      </form>
    </section>
  );
}
