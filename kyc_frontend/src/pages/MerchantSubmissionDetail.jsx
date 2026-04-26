import React, { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { kycAPI } from '../api';

const MerchantSubmissionDetail = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const [submission, setSubmission] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

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

  const canEdit = submission && submission.status === 'draft' || submission?.status === 'more_info_requested';
  const canResubmit = submission && submission.status === 'more_info_requested';

  if (loading) {
    return <div className="flex justify-center items-center h-screen">Loading...</div>;
  }

  if (!submission) {
    return (
      <div className="flex flex-col items-center justify-center h-screen">
        <p className="text-gray-600 mb-4">Submission not found</p>
        <button
          onClick={() => navigate('/merchant/dashboard')}
          className="bg-blue-600 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded-lg"
        >
          Back to Dashboard
        </button>
      </div>
    );
  }

  const getStatusColor = (status) => {
    const colors = {
      draft: 'bg-gray-100 text-gray-800 border-gray-300',
      submitted: 'bg-blue-100 text-blue-800 border-blue-300',
      under_review: 'bg-yellow-100 text-yellow-800 border-yellow-300',
      approved: 'bg-green-100 text-green-800 border-green-300',
      rejected: 'bg-red-100 text-red-800 border-red-300',
      more_info_requested: 'bg-orange-100 text-orange-800 border-orange-300',
    };
    return colors[status] || colors.draft;
  };

  const getStatusLabel = (status) => {
    const labels = {
      draft: '📝 Draft',
      submitted: '📬 Submitted',
      under_review: '🔍 Under Review',
      approved: '✅ Approved',
      rejected: '❌ Rejected',
      more_info_requested: 'ℹ️ More Info Requested',
    };
    return labels[status] || status;
  };

  return (
    <div className="min-h-screen bg-gray-100">
      {/* Header */}
      <header className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-6 py-4 flex justify-between items-center">
          <h1 className="text-2xl font-bold text-gray-800">Submission #{submission.id}</h1>
          <button
            onClick={() => navigate('/merchant/dashboard')}
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

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Details */}
          <div className="lg:col-span-2 space-y-6">
            {/* Personal Info */}
            <div className="bg-white rounded-lg shadow p-6">
              <h2 className="text-xl font-semibold mb-4 text-gray-800">Personal Information</h2>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                <div>
                  <p className="text-gray-600 font-semibold">Full Name</p>
                  <p className="text-gray-800 mt-1">{submission.name}</p>
                </div>
                <div>
                  <p className="text-gray-600 font-semibold">Email</p>
                  <p className="text-gray-800 mt-1">{submission.email}</p>
                </div>
                <div>
                  <p className="text-gray-600 font-semibold">Phone</p>
                  <p className="text-gray-800 mt-1">{submission.phone}</p>
                </div>
              </div>
            </div>

            {/* Business Info */}
            <div className="bg-white rounded-lg shadow p-6">
              <h2 className="text-xl font-semibold mb-4 text-gray-800">Business Information</h2>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                <div>
                  <p className="text-gray-600 font-semibold">Business Name</p>
                  <p className="text-gray-800 mt-1">{submission.business_name}</p>
                </div>
                <div>
                  <p className="text-gray-600 font-semibold">Business Type</p>
                  <p className="text-gray-800 mt-1">{submission.business_type}</p>
                </div>
                <div>
                  <p className="text-gray-600 font-semibold">Monthly Volume</p>
                  <p className="text-gray-800 mt-1">
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

            {/* Activity Log */}
            {submission.notifications.length > 0 && (
              <div className="bg-white rounded-lg shadow p-6">
                <h2 className="text-xl font-semibold mb-4 text-gray-800">Activity Log</h2>
                <div className="space-y-3 max-h-64 overflow-y-auto">
                  {submission.notifications.map((notif) => (
                    <div key={notif.id} className="p-3 border-l-4 border-blue-500 bg-blue-50">
                      <p className="font-semibold text-gray-800 text-sm">
                        {notif.event_type.replace(/_/g, ' ').toUpperCase()}
                      </p>
                      <p className="text-xs text-gray-600 mt-1">
                        {new Date(notif.created_at).toLocaleString()}
                      </p>
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
              <div className={`p-4 rounded-lg text-center border-2 ${getStatusColor(submission.status)}`}>
                <p className="font-bold text-lg">{getStatusLabel(submission.status)}</p>
              </div>

              <div className="mt-4 space-y-2 text-xs text-gray-600">
                <p><strong>Created:</strong> {new Date(submission.created_at).toLocaleString()}</p>
                {submission.submitted_at && (
                  <p><strong>Submitted:</strong> {new Date(submission.submitted_at).toLocaleString()}</p>
                )}
                {submission.reviewed_at && (
                  <p><strong>Reviewed:</strong> {new Date(submission.reviewed_at).toLocaleString()}</p>
                )}
              </div>
            </div>

            {/* Actions */}
            {canEdit && (
              <div className="bg-white rounded-lg shadow p-6">
                <h3 className="text-lg font-semibold mb-4 text-gray-800">Actions</h3>
                <button
                  onClick={() => navigate(`/merchant/edit/${submission.id}`)}
                  className="w-full bg-blue-600 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded-lg transition mb-2"
                >
                  Edit Information
                </button>
                <p className="text-xs text-gray-600">
                  You can edit your information or upload/replace documents.
                </p>
              </div>
            )}

            {/* Reviewer Notes */}
            {submission.reviewer_notes && (
              <div className="bg-orange-50 border-2 border-orange-300 rounded-lg p-6">
                <h3 className="text-lg font-semibold mb-3 text-orange-900">Reviewer Notes</h3>
                <p className="text-orange-900 text-sm">{submission.reviewer_notes}</p>
                
                {canResubmit && (
                  <button
                    onClick={() => navigate(`/merchant/edit/${submission.id}`)}
                    className="mt-4 w-full bg-orange-600 hover:bg-orange-700 text-white font-bold py-2 px-4 rounded-lg transition"
                  >
                    Update & Resubmit
                  </button>
                )}
              </div>
            )}

            {/* Status Info */}
            {submission.status === 'draft' && (
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                <p className="text-sm text-blue-900">
                  You can edit this submission and upload documents. Once ready, submit for review.
                </p>
              </div>
            )}

            {submission.status === 'submitted' && (
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                <p className="text-sm text-blue-900">
                  Your submission has been sent for review. You'll be notified once it's been reviewed.
                </p>
              </div>
            )}

            {submission.status === 'under_review' && (
              <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
                <p className="text-sm text-yellow-900">
                  Your submission is currently being reviewed. Please wait for updates.
                </p>
              </div>
            )}

            {submission.status === 'approved' && (
              <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                <p className="text-sm font-semibold text-green-900">
                  ✅ Congratulations! Your KYC has been approved.
                </p>
              </div>
            )}

            {submission.status === 'rejected' && (
              <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                <p className="text-sm font-semibold text-red-900">
                  ❌ Your submission has been rejected.
                </p>
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  );
};

export default MerchantSubmissionDetail;
