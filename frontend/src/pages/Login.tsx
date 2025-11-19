import React from "react";

import { useState } from "react";

interface LoginProps {
  onLogin: (credentials: { username: string; password: string }) => Promise<void>;
  loading?: boolean;
  error?: string | null;
}

export default function Login({ onLogin, loading, error }: LoginProps) {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    try {
      await onLogin({ username, password });
    } catch {
      // errors are surfaced via props
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-slate-950 px-4 py-10">
      <div className="w-full max-w-md rounded-3xl border border-white/5 bg-white/5 p-8 text-white shadow-2xl backdrop-blur-xl">
        <div className="mb-6 text-center">
          <p className="text-sm uppercase tracking-[0.4em] text-slate-400">WQAM</p>
          <h1 className="mt-2 text-3xl font-semibold">Operator Console</h1>
          <p className="mt-2 text-sm text-slate-400">Sign in to monitor water quality across sites.</p>
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
            {loading ? "Signing in..." : "Enter dashboard"}
          </button>
        </form>

        <p className="mt-6 text-center text-xs text-slate-500">
          Tip: use <span className="font-semibold text-slate-200">admin / adminpass</span> or any user seeded in the backend.
        </p>
      </div>
    </div>
  );
}
