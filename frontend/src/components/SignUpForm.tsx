import React, { useState } from 'react';

const SignUpForm = ({ onSignUp, loading, error, onBack }: {
  onSignUp: (credentials: { username: string; password: string; role: string }) => void;
  loading: boolean;
  error: string | null;
  onBack: () => void;
}) => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [role, setRole] = useState('user'); // Default role

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (password !== confirmPassword) {
      alert("Passwords do not match!");
      return;
    }
    onSignUp({ username, password, role });
  };

  return (
    <div className="w-full max-w-md bg-white/5 backdrop-blur-lg rounded-2xl shadow-2xl p-8 transform-gpu">
      <button onClick={onBack} className="absolute top-4 left-4 text-slate-400 hover:text-white transition-colors">&larr; Back</button>
      <div className="text-center mb-8">
        <h2 className="text-3xl font-bold text-white">Sign Up</h2>
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
        <div className="mb-4">
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
        <div className="mb-6">
          <label className="block text-slate-300 text-sm font-bold mb-2" htmlFor="confirmPassword">
            Confirm Password
          </label>
          <input
            id="confirmPassword"
            type="password"
            value={confirmPassword}
            onChange={(e) => setConfirmPassword(e.target.value)}
            className="shadow-inner appearance-none border border-white/10 rounded-lg w-full py-3 px-4 bg-black/20 text-white leading-tight focus:outline-none focus:ring-2 focus:ring-blue-500"
            required
          />
        </div>
        <div className="mb-6">
          <label className="block text-slate-300 text-sm font-bold mb-2" htmlFor="role">
            Role
          </label>
          <select
            id="role"
            value={role}
            onChange={(e) => setRole(e.target.value)}
            className="shadow-inner appearance-none border border-white/10 rounded-lg w-full py-3 px-4 bg-black/20 text-white leading-tight focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="user">User</option>
            <option value="validator">Validator</option>
            <option value="business">Business</option>
            <option value="plant">STP/WTP Plant</option>
          </select>
        </div>
        {error && (
          <p className="bg-red-500/20 text-red-300 text-xs italic p-3 rounded-md mb-4 text-center">{error}</p>
        )}
        <div className="flex items-center justify-between">
          <button
            type="submit"
            disabled={loading}
            className="w-full bg-green-600 hover:bg-green-700 text-white font-bold py-3 px-4 rounded-lg focus:outline-none focus:shadow-outline transition-all duration-300 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? 'Signing Up...' : 'Sign Up'}
          </button>
        </div>
      </form>
    </div>
  );
};

export default SignUpForm;
