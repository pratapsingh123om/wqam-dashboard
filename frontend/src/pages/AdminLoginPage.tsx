import React from "react";
import { useState } from "react";

interface AdminLoginProps {
  onLogin: (credentials: { username: string; password: string }) => Promise<void>;
  loading?: boolean;
  error?: string | null;
}

export default function AdminLoginPage({ onLogin, loading, error }: AdminLoginProps) {
  const [username, setUsername] = useState("admin");
  const [password, setPassword] = useState("admin123");

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    try {
      await onLogin({ username, password });
    } catch {
      // errors are surfaced via props
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-gradient-to-br from-purple-600 to-blue-600 px-4 py-10">
      <div className="w-full max-w-md rounded-3xl border border-white/5 bg-slate-800 p-8 text-white shadow-2xl backdrop-blur-xl">
        <div className="mb-6 text-center">
          <p className="text-sm uppercase tracking-[0.4em] text-slate-400">WQAM</p>
          <h1 className="mt-2 text-3xl font-semibold">Admin Console</h1>
          <p className="mt-2 text-sm text-slate-400">Sign in to manage users and system settings.</p>
        </div>

        <form className="space-y-5" onSubmit={handleSubmit}>
          <div>
            <label className="text-xs uppercase tracking-wide text-slate-400">
              Username
              <input
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                className="mt-2 w-full rounded-xl border border-white/10 bg-white/5 px-4 py-3 text-base outline-none focus:border-white/40"
                placeholder="admin"
                autoComplete="username"
                required
              />
            </label>
          </div>
          <div>
            <label className="text-xs uppercase tracking-wide text-slate-400">
              Password
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="mt-2 w-full rounded-xl border border-white/10 bg-white/5 px-4 py-3 text-base outline-none focus:border-white/40"
                placeholder="••••••••"
                autoComplete="current-password"
                required
              />
            </label>
          </div>

          {error && (
            <div className="rounded-xl border border-rose-500/30 bg-rose-500/10 px-4 py-3 text-sm text-rose-200">
              {error}
            </div>
          )}

          <button
            type="submit"
            disabled={loading}
            className="w-full rounded-2xl bg-blue-600 py-3 text-lg font-semibold shadow-lg shadow-blue-600/30 transition hover:bg-blue-500 disabled:cursor-not-allowed disabled:opacity-50"
          >
            {loading ? "Signing in..." : "Enter Console"}
          </button>
        </form>
      </div>
    </div>
  );
}
