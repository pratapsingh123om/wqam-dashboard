import { useState, useEffect, useCallback } from 'react';
import { getPendingUsers, approveUser } from '../services/admin';

interface User {
  id: number;
  username: string;
  role: string;
}

const AdminDashboard = () => {
  const [pendingUsers, setPendingUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchUsers = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const users = await getPendingUsers();
      setPendingUsers(users);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch pending users.');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchUsers();
  }, [fetchUsers]);

  const handleApprove = async (userId: number) => {
    try {
      await approveUser(userId);
      // Remove the user from the list on successful approval
      setPendingUsers(prevUsers => prevUsers.filter(user => user.id !== userId));
    } catch (err) {
      alert(`Failed to approve user: ${err instanceof Error ? err.message : 'Unknown error'}`);
    }
  };

  if (loading) {
    return <div className="text-center p-8">Loading pending users...</div>;
  }

  if (error) {
    return <div className="text-center p-8 text-red-400">Error: {error}</div>;
  }

  return (
    <div className="p-4 sm:p-6">
      <h1 className="text-2xl font-bold text-white mb-6">Pending User Approvals</h1>
      {pendingUsers.length === 0 ? (
        <p className="text-slate-400">There are no pending users to approve.</p>
      ) : (
        <div className="overflow-x-auto bg-slate-800/50 rounded-lg shadow-lg">
          <table className="min-w-full text-sm text-left text-slate-300">
            <thead className="text-xs text-slate-400 uppercase bg-slate-900/50">
              <tr>
                <th scope="col" className="px-6 py-3">Username</th>
                <th scope="col" className="px-6 py-3">Role</th>
                <th scope="col" className="px-6 py-3 text-right">Action</th>
              </tr>
            </thead>
            <tbody>
              {pendingUsers.map(user => (
                <tr key={user.id} className="border-b border-slate-700 hover:bg-slate-800">
                  <td className="px-6 py-4 font-medium text-white">{user.username}</td>
                  <td className="px-6 py-4 capitalize">{user.role}</td>
                  <td className="px-6 py-4 text-right">
                    <button
                      onClick={() => handleApprove(user.id)}
                      className="font-medium text-blue-500 hover:text-blue-400 transition-colors"
                    >
                      Approve
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};

export default AdminDashboard;
