import React, { useState } from 'react';

const LoginForm = ({ role, onLogin, loading, error, onBack, onShowSignup }: {
  role: string;
  onLogin: (credentials: { username: string; password: string }) => void;
  loading: boolean;
  error: string | null;
  onBack: () => void;
  onShowSignup: () => void; // Added this line
}) => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onLogin({ username, password });
  };

  return (
    <div className="w-full max-w-md bg-white/5 backdrop-blur-lg rounded-2xl shadow-2xl p-8 transform-gpu">
      <button onClick={onBack} className="absolute top-4 left-4 text-slate-400 hover:text-white transition-colors">&larr; Back</button>
      <div className="text-center mb-8">
        <h2 className="text-3xl font-bold text-white">{role} Login</h2>
      </div>

      <form onSubmit={handleSubmit}>
        <div className="mb-4">
          <label className="block text-slate-300 text-sm font-bold mb-2" htmlFor="username">
            Username
          </label>
          <input
            id="username"
            type="text"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            className="shadow-inner appearance-none border border-white/10 rounded-lg w-full py-3 px-4 bg-black/20 text-white leading-tight focus:outline-none focus:ring-2 focus:ring-blue-500"
            required
          />
        </div>
        <div className="mb-6">
          <label className="block text-slate-300 text-sm font-bold mb-2" htmlFor="password">
            Password
          </label>
          <input
            id="password"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="shadow-inner appearance-none border border-white/10 rounded-lg w-full py-3 px-4 bg-black/20 text-white leading-tight focus:outline-none focus:ring-2 focus:ring-blue-500"
            required
          />
        </div>
        {error && (
          <p className="bg-red-500/20 text-red-300 text-xs italic p-3 rounded-md mb-4 text-center">{error}</p>
        )}
        <div className="flex items-center justify-between">
          <button
            type="submit"
            disabled={loading}
            className="w-full bg-blue-600 hover:bg-blue-700 text-white font-bold py-3 px-4 rounded-lg focus:outline-none focus:shadow-outline transition-all duration-300 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? 'Logging in...' : 'Log In'}
          </button>
        </div>
        <div className="text-center mt-4">
          <button
            type="button"
            onClick={onShowSignup}
            className="text-slate-400 hover:text-white transition-colors duration-300 font-semibold text-sm"
          >
            Don't have an account? Sign Up
          </button>
        </div>
      </form>
    </div>
  );
};

export default LoginForm;
