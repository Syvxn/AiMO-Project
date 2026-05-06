export default function RegisterPage() {
  return (
    <section className="space-y-6">
      <h1 className="font-display text-4xl">Register</h1>
      <form className="card max-w-xl space-y-4">
        <div className="grid gap-4 sm:grid-cols-2">
          <div className="space-y-1">
            <label htmlFor="name" className="text-sm text-slate-300">Display Name</label>
            <input id="name" type="text" className="w-full rounded-md border border-white/20 bg-slate-950/60 px-3 py-2" />
          </div>
          <div className="space-y-1">
            <label htmlFor="email" className="text-sm text-slate-300">Email</label>
            <input id="email" type="email" className="w-full rounded-md border border-white/20 bg-slate-950/60 px-3 py-2" />
          </div>
        </div>
        <div className="space-y-1">
          <label htmlFor="password" className="text-sm text-slate-300">Password</label>
          <input id="password" type="password" className="w-full rounded-md border border-white/20 bg-slate-950/60 px-3 py-2" />
        </div>
        <div className="space-y-1">
          <label htmlFor="role" className="text-sm text-slate-300">Role</label>
          <select id="role" className="w-full rounded-md border border-white/20 bg-slate-950/60 px-3 py-2">
            <option value="student">Student</option>
            <option value="teacher">Teacher</option>
            <option value="admin">Admin</option>
          </select>
        </div>
        <button className="btn-primary" type="submit">Create Account</button>
      </form>
    </section>
  );
}
