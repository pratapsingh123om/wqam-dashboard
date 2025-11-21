import React, { useEffect, useState } from 'react';
import { api } from '../services/api'; // Assuming you have an api service
import type { User } from '../types'; // Assuming you have a User type

const AdminDashboardPage: React.FC = () => {
  const [pendingUsers, setPendingUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchPendingUsers = async () => {
    try {
      setLoading(true);
      const response = await api.get<User[]>('/admin/pending-users');
      setPendingUsers(response.data);
      setError(null);
    } catch (err) {
      setError('Failed to fetch pending users. You may not have administrative rights.');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPendingUsers();
  }, []);

  const handleApproveUser = async (userId: number) => {
    try {
      await api.post(`/admin/approve-user/${userId}`);
      // Refresh the list after approval
      fetchPendingUsers();
    } catch (err) {
      setError(`Failed to approve user ${userId}.`);
      console.error(err);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-600 to-blue-600 text-white p-8">
      <div className="max-w-4xl mx-auto rounded-3xl border border-white/5 bg-slate-800 p-8 text-white shadow-2xl backdrop-blur-xl">
        <h1 className="text-3xl font-bold mb-6">Admin Dashboard</h1>
        <h2 className="text-xl font-semibold mb-4">Pending User Approvals</h2>

        {loading && <p>Loading...</p>}
        {error && <p className="text-red-500">{error}</p>}

        {!loading && !error && (
          <div className="bg-slate-700 rounded-lg shadow-lg p-6">
            {pendingUsers.length === 0 ? (
              <p>No users are currently pending approval.</p>
            ) : (
              <ul className="divide-y divide-slate-600">
                {pendingUsers.map((user) => (
                  <li key={user.id} className="py-4 flex items-center justify-between">
                    <div>
                      <p className="font-semibold">{user.username}</p>
                      <p className="text-sm text-slate-300">Role: {user.role}</p>
                    </div>
                    <button
                      onClick={() => handleApproveUser(user.id)}
                      className="bg-green-600 hover:bg-green-500 text-white font-bold py-2 px-4 rounded-lg transition"
                    >
                      Approve
                    </button>
                  </li>
                ))}
              </ul>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default AdminDashboardPage;
