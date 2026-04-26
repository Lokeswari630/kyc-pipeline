import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { kycAPI } from '../api';
import { useAuth } from '../context/AuthContext';

const ReviewerDashboard = () => {
  const navigate = useNavigate();
  const { user, logout } = useAuth();
  const [queue, setQueue] = useState([]);
  const [metrics, setMetrics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [atRiskOnly, setAtRiskOnly] = useState(false);
  const [ordering, setOrdering] = useState('oldest');

  const fetchQueue = useCallback(async () => {
    try {
      const params = {
        ordering,
      };

      if (search.trim()) {
        params.search = search.trim();
      }
      if (statusFilter !== 'all') {
        params.status = statusFilter;
      }
      if (atRiskOnly) {
        params.at_risk_only = true;
      }

      const response = await kycAPI.getQueue(params);
      setQueue(response.data.queue);
      setMetrics(response.data.metrics);
    } catch (err) {
      setError('Failed to load queue');
    } finally {
      setLoading(false);
    }
  }, [search, statusFilter, atRiskOnly, ordering]);

  useEffect(() => {
    fetchQueue();
    const interval = setInterval(fetchQueue, 30000); // Refresh every 30 seconds
    return () => clearInterval(interval);
  }, [fetchQueue]);

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const getAtRiskLabel = (submission) => {
    if (!submission.submitted_at) return null;
    const submitted = new Date(submission.submitted_at);
    const now = new Date();
    const hoursInQueue = (now - submitted) / (1000 * 60 * 60);
    return hoursInQueue > 24 ? '⚠️ At Risk' : null;
  };

  if (loading) {
    return <div className="flex justify-center items-center h-screen">Loading...</div>;
  }

  return (
    <div className="min-h-screen bg-gray-100">
      {/* Header */}
      <header className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-6 py-4 flex justify-between items-center">
          <div>
            <h1 className="text-2xl font-bold text-gray-800">Reviewer Dashboard</h1>
            <p className="text-gray-600">Welcome, {user?.username}!</p>
          </div>
          <button
            onClick={handleLogout}
            className="bg-red-600 hover:bg-red-700 text-white font-bold py-2 px-4 rounded-lg transition"
          >
            Logout
          </button>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-6 py-8">
        {error && (
          <div className="mb-4 p-4 bg-red-100 border border-red-400 text-red-700 rounded">
            {error}
          </div>
        )}

        {/* Metrics */}
        {metrics && (
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
            <div className="bg-white rounded-lg shadow p-6">
              <h3 className="text-gray-600 text-sm font-semibold mb-2">In Queue</h3>
              <p className="text-3xl font-bold text-blue-600">{metrics.total_in_queue}</p>
              <p className="text-xs text-gray-500 mt-2">Submitted & Under Review</p>
            </div>
            
            <div className="bg-white rounded-lg shadow p-6">
              <h3 className="text-gray-600 text-sm font-semibold mb-2">Avg Time in Queue</h3>
              <p className="text-3xl font-bold text-purple-600">{metrics.average_time_in_queue_hours}h</p>
              <p className="text-xs text-gray-500 mt-2">Average hours</p>
            </div>

            <div className="bg-white rounded-lg shadow p-6">
              <h3 className="text-gray-600 text-sm font-semibold mb-2">Approval Rate (7d)</h3>
              <p className="text-3xl font-bold text-green-600">{metrics.approval_rate_7days}%</p>
              <p className="text-xs text-gray-500 mt-2">Last 7 days</p>
            </div>

            <div className="bg-white rounded-lg shadow p-6">
              <h3 className="text-gray-600 text-sm font-semibold mb-2">At Risk</h3>
              <p className={`text-3xl font-bold ${metrics.at_risk_count > 0 ? 'text-red-600' : 'text-green-600'}`}>
                {metrics.at_risk_count}
              </p>
              <p className="text-xs text-gray-500 mt-2">&gt; 24 hours in queue</p>
            </div>
          </div>
        )}

        {/* Queue */}
        <div className="bg-white rounded-lg shadow">
          <div className="p-6 border-b border-gray-200">
            <h2 className="text-2xl font-semibold text-gray-800">Submissions Queue</h2>
            <p className="text-gray-600 text-sm mt-1">
              Showing {queue.length} submission{queue.length !== 1 ? 's' : ''}
              {metrics ? ` (Total in queue: ${metrics.total_in_queue})` : ''}
            </p>
            <div className="mt-4 grid grid-cols-1 md:grid-cols-4 gap-3">
              <input
                type="text"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder="Search business, merchant, email..."
                className="md:col-span-2 px-3 py-2 border border-gray-300 rounded-lg"
              />
              <select
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
                className="px-3 py-2 border border-gray-300 rounded-lg"
              >
                <option value="all">All Queue Statuses</option>
                <option value="submitted">Submitted</option>
                <option value="under_review">Under Review</option>
              </select>
              <select
                value={ordering}
                onChange={(e) => setOrdering(e.target.value)}
                className="px-3 py-2 border border-gray-300 rounded-lg"
              >
                <option value="oldest">Oldest First</option>
                <option value="newest">Newest First</option>
                <option value="high_volume">Highest Volume</option>
                <option value="low_volume">Lowest Volume</option>
              </select>
            </div>
            <div className="mt-3 flex items-center gap-2">
              <input
                id="atRiskOnly"
                type="checkbox"
                checked={atRiskOnly}
                onChange={(e) => setAtRiskOnly(e.target.checked)}
                className="h-4 w-4"
              />
              <label htmlFor="atRiskOnly" className="text-sm text-gray-700">
                Show only at-risk submissions (&gt; 24h)
              </label>
            </div>
          </div>

          {queue.length === 0 ? (
            <div className="p-8 text-center text-gray-600">
              <p>No submissions in queue</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-gray-50 border-b border-gray-200">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-semibold text-gray-700">ID</th>
                    <th className="px-6 py-3 text-left text-xs font-semibold text-gray-700">Business</th>
                    <th className="px-6 py-3 text-left text-xs font-semibold text-gray-700">Contact</th>
                    <th className="px-6 py-3 text-left text-xs font-semibold text-gray-700">Status</th>
                    <th className="px-6 py-3 text-left text-xs font-semibold text-gray-700">Time in Queue</th>
                    <th className="px-6 py-3 text-left text-xs font-semibold text-gray-700">Risk</th>
                    <th className="px-6 py-3 text-left text-xs font-semibold text-gray-700">Action</th>
                  </tr>
                </thead>
                <tbody>
                  {queue.map((submission) => {
                    const submitted = new Date(submission.submitted_at);
                    const now = new Date();
                    const hoursInQueue = ((now - submitted) / (1000 * 60 * 60)).toFixed(1);
                    const risk = getAtRiskLabel(submission);

                    return (
                      <tr key={submission.id} className="border-b border-gray-200 hover:bg-gray-50">
                        <td className="px-6 py-4 text-sm text-gray-800 font-semibold">
                          {submission.id}
                        </td>
                        <td className="px-6 py-4 text-sm">
                          <p className="text-gray-800 font-semibold">{submission.business_name}</p>
                          <p className="text-gray-600 text-xs">{submission.business_type}</p>
                        </td>
                        <td className="px-6 py-4 text-sm">
                          <p className="text-gray-800">{submission.name}</p>
                          <p className="text-gray-600 text-xs">{submission.email}</p>
                        </td>
                        <td className="px-6 py-4 text-sm">
                          <span className={`px-3 py-1 rounded-full text-xs font-semibold ${
                            submission.status === 'submitted' 
                              ? 'bg-blue-200 text-blue-800' 
                              : 'bg-yellow-200 text-yellow-800'
                          }`}>
                            {submission.status === 'submitted' ? 'Submitted' : 'Under Review'}
                          </span>
                        </td>
                        <td className="px-6 py-4 text-sm text-gray-800">
                          {hoursInQueue}h
                        </td>
                        <td className="px-6 py-4 text-sm">
                          {risk ? <span className="font-semibold text-red-600">{risk}</span> : '-'}
                        </td>
                        <td className="px-6 py-4 text-sm">
                          <button
                            onClick={() => navigate(`/reviewer/submission/${submission.id}`)}
                            className="bg-blue-600 hover:bg-blue-700 text-white px-3 py-1 rounded text-xs transition"
                          >
                            Review
                          </button>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </main>
    </div>
  );
};

export default ReviewerDashboard;
