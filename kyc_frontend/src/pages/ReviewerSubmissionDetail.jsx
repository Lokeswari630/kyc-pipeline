import React, { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { kycAPI } from '../api';

const ReviewerSubmissionDetail = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const [submission, setSubmission] = useState(null);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [action, setAction] = useState('');
  const [notes, setNotes] = useState('');

  useEffect(() => {
    fetchSubmission();
  }, [id]);

  const fetchSubmission = async () => {
    try {
      const response = await kycAPI.getSubmission(id);
      setSubmission(response.data);
    } catch (err) {
      setError('Failed to load submission');
    } finally {
      setLoading(false);
    }
  };

  const handleChangeStatus = async (e) => {
    e.preventDefault();
    setSubmitting(true);
    setError('');
    setSuccess('');

    try {
      if (!action) {
        setError('Please select an action');
        setSubmitting(false);
        return;
      }

      const newStatus = action;

      const response = await kycAPI.changeStatus(id, newStatus, notes);
      setSubmission(response.data);
      setSuccess(`Status updated to ${newStatus}!`);
      setAction('');
      setNotes('');
      setTimeout(() => navigate('/reviewer/dashboard'), 2000);
    } catch (err) {
      const message = err.response?.data?.error || 'Failed to update status';
      setError(typeof message === 'object' ? Object.values(message)[0] : message);
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return <div className="flex justify-center items-center h-screen">Loading...</div>;
  }

  if (!submission) {
    return (
      <div className="flex flex-col items-center justify-center h-screen">
        <p className="text-gray-600 mb-4">Submission not found</p>
        <button
          onClick={() => navigate('/reviewer/dashboard')}
          className="bg-blue-600 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded-lg"
        >
          Back to Dashboard
        </button>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-100">
      {/* Header */}
      <header className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-6 py-4 flex justify-between items-center">
          <h1 className="text-2xl font-bold text-gray-800">Review Submission #{submission.id}</h1>
          <button
            onClick={() => navigate('/reviewer/dashboard')}
            className="bg-gray-600 hover:bg-gray-700 text-white font-bold py-2 px-4 rounded-lg"
          >
            Back
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

        {success && (
          <div className="mb-4 p-4 bg-green-100 border border-green-400 text-green-700 rounded">
            {success}
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Details */}
          <div className="lg:col-span-2 space-y-6">
            {/* Personal Info */}
            <div className="bg-white rounded-lg shadow p-6">
              <h2 className="text-xl font-semibold mb-4 text-gray-800">Personal Information</h2>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                <div>
                  <p className="text-gray-600">Full Name</p>
                  <p className="font-semibold text-gray-800">{submission.name}</p>
                </div>
                <div>
                  <p className="text-gray-600">Email</p>
                  <p className="font-semibold text-gray-800">{submission.email}</p>
                </div>
                <div>
                  <p className="text-gray-600">Phone</p>
                  <p className="font-semibold text-gray-800">{submission.phone}</p>
                </div>
              </div>
            </div>

            {/* Business Info */}
            <div className="bg-white rounded-lg shadow p-6">
              <h2 className="text-xl font-semibold mb-4 text-gray-800">Business Information</h2>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                <div>
                  <p className="text-gray-600">Business Name</p>
                  <p className="font-semibold text-gray-800">{submission.business_name}</p>
                </div>
                <div>
                  <p className="text-gray-600">Business Type</p>
                  <p className="font-semibold text-gray-800">{submission.business_type}</p>
                </div>
                <div>
                  <p className="text-gray-600">Monthly Volume</p>
                  <p className="font-semibold text-gray-800">
                    ₹{parseFloat(submission.monthly_volume).toLocaleString('en-IN')}
                  </p>
                </div>
              </div>
            </div>

            {/* Documents */}
            <div className="bg-white rounded-lg shadow p-6">
              <h2 className="text-xl font-semibold mb-4 text-gray-800">Documents</h2>
              {submission.documents.length === 0 ? (
                <p className="text-gray-600">No documents uploaded</p>
              ) : (
                <div className="space-y-3">
                  {submission.documents.map((doc) => (
                    <div key={doc.id} className="p-3 border border-gray-200 rounded flex items-center justify-between">
                      <div>
                        <p className="font-semibold text-gray-800">
                          {doc.document_type === 'bank_statement' ? 'Bank Statement' : doc.document_type.toUpperCase()}
                        </p>
                        <p className="text-xs text-gray-600">
                          Uploaded {new Date(doc.uploaded_at).toLocaleDateString()}
                        </p>
                      </div>
                      <a
                        href={`http://localhost:8000${doc.file}`}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-blue-600 hover:text-blue-800 font-semibold text-sm"
                      >
                        View
                      </a>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Notifications */}
            {submission.notifications.length > 0 && (
              <div className="bg-white rounded-lg shadow p-6">
                <h2 className="text-xl font-semibold mb-4 text-gray-800">Activity Log</h2>
                <div className="space-y-3 max-h-64 overflow-y-auto">
                  {submission.notifications.map((notif) => (
                    <div key={notif.id} className="p-3 border-l-4 border-blue-500 bg-blue-50">
                      <div className="flex justify-between items-start">
                        <div>
                          <p className="font-semibold text-gray-800">{notif.event_type}</p>
                          <p className="text-xs text-gray-600">
                            {new Date(notif.created_at).toLocaleString()}
                          </p>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Sidebar */}
          <div className="space-y-6">
            {/* Status */}
            <div className="bg-white rounded-lg shadow p-6">
              <h3 className="text-lg font-semibold mb-4 text-gray-800">Status</h3>
              <div className="p-3 bg-yellow-50 border-2 border-yellow-200 rounded-lg text-center">
                <p className="text-yellow-800 font-bold">
                  {submission.status === 'submitted' ? 'SUBMITTED' : 'UNDER REVIEW'}
                </p>
              </div>
              <p className="text-xs text-gray-600 mt-2">
                Submitted: {new Date(submission.submitted_at).toLocaleString()}
              </p>
            </div>

            {/* Actions */}
            <div className="bg-white rounded-lg shadow p-6">
              <h3 className="text-lg font-semibold mb-4 text-gray-800">Review Actions</h3>

              {submission.status !== 'approved' && submission.status !== 'rejected' ? (
                <form onSubmit={handleChangeStatus} className="space-y-4">
                  {/* First move to Under Review if Submitted */}
                  {submission.status === 'submitted' && (
                    <button
                      type="button"
                      onClick={() => setAction('under_review')}
                      className={`w-full py-2 px-4 rounded-lg font-semibold transition ${
                        action === 'under_review'
                          ? 'bg-yellow-600 text-white'
                          : 'bg-gray-200 text-gray-800 hover:bg-gray-300'
                      }`}
                    >
                      Start Review
                    </button>
                  )}

                  {/* Final decisions */}
                  {submission.status === 'under_review' && (
                    <>
                      <button
                        type="button"
                        onClick={() => setAction('approved')}
                        className={`w-full py-2 px-4 rounded-lg font-semibold transition ${
                          action === 'approved'
                            ? 'bg-green-600 text-white'
                            : 'bg-gray-200 text-gray-800 hover:bg-gray-300'
                        }`}
                      >
                        ✓ Approve
                      </button>

                      <button
                        type="button"
                        onClick={() => setAction('rejected')}
                        className={`w-full py-2 px-4 rounded-lg font-semibold transition ${
                          action === 'rejected'
                            ? 'bg-red-600 text-white'
                            : 'bg-gray-200 text-gray-800 hover:bg-gray-300'
                        }`}
                      >
                        ✗ Reject
                      </button>

                      <button
                        type="button"
                        onClick={() => setAction('more_info_requested')}
                        className={`w-full py-2 px-4 rounded-lg font-semibold transition ${
                          action === 'more_info_requested'
                            ? 'bg-orange-600 text-white'
                            : 'bg-gray-200 text-gray-800 hover:bg-gray-300'
                        }`}
                      >
                        ⓘ Request Info
                      </button>
                    </>
                  )}

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Reviewer Notes
                    </label>
                    <textarea
                      value={notes}
                      onChange={(e) => setNotes(e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                      rows="4"
                      placeholder="Add notes for the merchant..."
                    />
                  </div>

                  <button
                    type="submit"
                    disabled={!action || submitting}
                    className="w-full bg-blue-600 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded-lg transition disabled:opacity-50"
                  >
                    {submitting ? 'Submitting...' : 'Submit Decision'}
                  </button>
                </form>
              ) : (
                <div className="p-4 bg-green-50 border border-green-200 rounded text-center">
                  <p className="text-green-800 font-semibold">
                    {submission.status === 'approved' ? '✓ APPROVED' : '✗ REJECTED'}
                  </p>
                  {submission.reviewed_at && (
                    <p className="text-xs text-green-700 mt-2">
                      {new Date(submission.reviewed_at).toLocaleString()}
                    </p>
                  )}
                </div>
              )}
            </div>

            {/* Previous Notes */}
            {submission.reviewer_notes && (
              <div className="bg-white rounded-lg shadow p-6">
                <h3 className="text-lg font-semibold mb-4 text-gray-800">Previous Notes</h3>
                <p className="text-gray-800 text-sm">{submission.reviewer_notes}</p>
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  );
};

export default ReviewerSubmissionDetail;
