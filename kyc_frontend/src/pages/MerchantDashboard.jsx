import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { kycAPI, notificationAPI } from '../api';
import { useAuth } from '../context/AuthContext';

const MerchantDashboard = () => {
  const navigate = useNavigate();
  const { user, logout } = useAuth();
  const [submissions, setSubmissions] = useState([]);
  const [notifications, setNotifications] = useState([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    try {
      const [submissionsResponse, notificationsResponse, unreadResponse] = await Promise.all([
        kycAPI.getMySubmissions(),
        notificationAPI.getNotifications({ is_read: false }),
        notificationAPI.getUnreadCount(),
      ]);
      setSubmissions(submissionsResponse.data);
      setNotifications(notificationsResponse.data.results || []);
      setUnreadCount(unreadResponse.data.unread_count || 0);
    } catch (err) {
      setError('Failed to load dashboard data');
    } finally {
      setLoading(false);
    }
  };

  const handleMarkAllRead = async () => {
    try {
      await notificationAPI.markAllRead();
      setNotifications([]);
      setUnreadCount(0);
    } catch (err) {
      setError('Failed to mark notifications as read');
    }
  };

  const handleMarkRead = async (notificationId) => {
    try {
      await notificationAPI.markRead(notificationId);
      setNotifications((prev) => prev.filter((notif) => notif.id !== notificationId));
      setUnreadCount((prev) => Math.max(0, prev - 1));
    } catch (err) {
      setError('Failed to mark notification as read');
    }
  };

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const getStatusBadge = (status) => {
    const colors = {
      draft: 'bg-gray-200 text-gray-800',
      submitted: 'bg-blue-200 text-blue-800',
      under_review: 'bg-yellow-200 text-yellow-800',
      approved: 'bg-green-200 text-green-800',
      rejected: 'bg-red-200 text-red-800',
      more_info_requested: 'bg-orange-200 text-orange-800',
    };
    return colors[status] || 'bg-gray-200 text-gray-800';
  };

  const getStatusLabel = (status) => {
    const labels = {
      draft: 'Draft',
      submitted: 'Submitted',
      under_review: 'Under Review',
      approved: 'Approved',
      rejected: 'Rejected',
      more_info_requested: 'More Info Requested',
    };
    return labels[status] || status;
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
            <h1 className="text-2xl font-bold text-gray-800">Merchant Dashboard</h1>
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

        <div className="flex justify-between items-center mb-6">
          <h2 className="text-2xl font-semibold text-gray-800">Your KYC Submissions</h2>
          <button
            onClick={() => navigate('/merchant/create')}
            className="bg-blue-600 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded-lg transition"
          >
            + New Submission
          </button>
        </div>

        <div className="bg-white rounded-lg shadow p-6 mb-6">
          <div className="flex justify-between items-center mb-3">
            <h3 className="text-lg font-semibold text-gray-800">
              Notifications ({unreadCount} unread)
            </h3>
            <button
              onClick={handleMarkAllRead}
              disabled={unreadCount === 0}
              className="text-sm bg-gray-100 hover:bg-gray-200 px-3 py-1 rounded disabled:opacity-50"
            >
              Mark all read
            </button>
          </div>

          {notifications.length === 0 ? (
            <p className="text-sm text-gray-600">No unread notifications.</p>
          ) : (
            <div className="space-y-2">
              {notifications.slice(0, 5).map((notif) => (
                <div key={notif.id} className="border border-gray-200 rounded p-3 flex justify-between items-center gap-3">
                  <div>
                    <p className="text-sm font-semibold text-gray-800">{notif.event_type.replaceAll('_', ' ')}</p>
                    <p className="text-xs text-gray-600">{new Date(notif.created_at).toLocaleString()}</p>
                    {notif.submission_id && (
                      <button
                        type="button"
                        onClick={() => navigate(`/merchant/submission/${notif.submission_id}`)}
                        className="text-xs text-blue-600 hover:text-blue-800 mt-1"
                      >
                        Open submission #{notif.submission_id}
                      </button>
                    )}
                  </div>
                  <button
                    onClick={() => handleMarkRead(notif.id)}
                    className="text-xs bg-blue-100 hover:bg-blue-200 px-2 py-1 rounded"
                  >
                    Mark read
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>

        {submissions.length === 0 ? (
          <div className="bg-white rounded-lg shadow p-8 text-center">
            <p className="text-gray-600 mb-4">No submissions yet</p>
            <button
              onClick={() => navigate('/merchant/create')}
              className="bg-blue-600 hover:bg-blue-700 text-white font-bold py-2 px-6 rounded-lg transition"
            >
              Create Your First Submission
            </button>
          </div>
        ) : (
          <div className="grid gap-6">
            {submissions.map((submission) => (
              <div
                key={submission.id}
                className="bg-white rounded-lg shadow p-6 hover:shadow-lg transition cursor-pointer"
                onClick={() => navigate(`/merchant/submission/${submission.id}`)}
              >
                <div className="flex justify-between items-start mb-4">
                  <div>
                    <h3 className="text-lg font-semibold text-gray-800">
                      {submission.business_name}
                    </h3>
                    <p className="text-gray-600 text-sm">ID: {submission.id}</p>
                  </div>
                  <span className={`px-3 py-1 rounded-full text-sm font-semibold ${getStatusBadge(submission.status)}`}>
                    {getStatusLabel(submission.status)}
                  </span>
                </div>

                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm text-gray-600 mb-4">
                  <div>
                    <p className="font-semibold text-gray-700">Contact</p>
                    <p>{submission.name}</p>
                    <p className="text-xs">{submission.email}</p>
                  </div>
                  <div>
                    <p className="font-semibold text-gray-700">Type</p>
                    <p>{submission.business_type}</p>
                  </div>
                  <div>
                    <p className="font-semibold text-gray-700">Monthly Volume</p>
                    <p>₹{parseFloat(submission.monthly_volume).toLocaleString('en-IN')}</p>
                  </div>
                  <div>
                    <p className="font-semibold text-gray-700">Created</p>
                    <p>{new Date(submission.created_at).toLocaleDateString()}</p>
                  </div>
                </div>

                {submission.reviewer_notes && (
                  <div className="p-3 bg-yellow-50 border border-yellow-200 rounded text-sm text-yellow-800">
                    <p className="font-semibold">Reviewer Notes:</p>
                    <p>{submission.reviewer_notes}</p>
                  </div>
                )}

                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    navigate(`/merchant/submission/${submission.id}`);
                  }}
                  className="mt-4 bg-blue-600 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded-lg transition"
                >
                  View Details
                </button>
              </div>
            ))}
          </div>
        )}
      </main>
    </div>
  );
};

export default MerchantDashboard;
