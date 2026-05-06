"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth-context";
import { loginUser } from "@/lib/api";

export default function LoginPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const { login } = useAuth();
  const router = useRouter();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setIsLoading(true);

    try {
      const response = await loginUser(email, password);
      login(response.access_token, email, response.role);
      router.push("/play");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Login failed");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <section className="space-y-6">
      <h1 className="font-display text-4xl text-text-natural">Login</h1>
      <form className="card max-w-md space-y-4" onSubmit={handleSubmit}>
        {error && <div className="text-accent-orange text-sm">{error}</div>}
        <div className="space-y-1">
          <label htmlFor="email" className="text-sm text-text-beige">
            Email
          </label>
          <input
            id="email"
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="w-full rounded-md border border-accent-orange/30 px-3 py-2"
            required
          />
        </div>
        <div className="space-y-1">
          <label htmlFor="password" className="text-sm text-text-beige">
            Password
          </label>
          <input
            id="password"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="w-full rounded-md border border-accent-orange/30 px-3 py-2"
            required
          />
        </div>
        <button className="btn-primary w-full" type="submit" disabled={isLoading}>
          {isLoading ? "Signing in..." : "Sign In"}
        </button>
        <p className="text-center text-sm text-text-beige">
          Do not have an account?{" "}
          <a href="/register" className="text-accent-yellow hover:text-accent-orange underline">
            Register
          </a>
        </p>
      </form>
      <div className="card max-w-md border-accent-teal/30 text-sm">
        <p className="font-semibold mb-2 text-accent-yellow">Test accounts:</p>
        <p className="text-text-beige">student@test.com / password123456</p>
        <p className="text-text-beige">teacher@test.com / password123456</p>
        <p className="text-text-beige">admin@test.com / password123456</p>
      </div>
    </section>
  );
}
