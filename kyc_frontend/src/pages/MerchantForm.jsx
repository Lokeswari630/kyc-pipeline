import React, { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { kycAPI } from '../api';

const MerchantForm = ({ isUpdate = false }) => {
  const { id } = useParams();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(isUpdate);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    phone: '',
    business_name: '',
    business_type: '',
    monthly_volume: '',
  });

  const [documents, setDocuments] = useState({
    pan: null,
    aadhaar: null,
    bank_statement: null,
  });

  const [uploadedDocs, setUploadedDocs] = useState({});
  const [submission, setSubmission] = useState(null);

  // Load existing submission if updating
  useEffect(() => {
    if (isUpdate && id) {
      fetchSubmission();
    }
  }, [id, isUpdate]);

  const fetchSubmission = async () => {
    try {
      const response = await kycAPI.getSubmission(id);
      setSubmission(response.data);
      setFormData({
        name: response.data.name,
        email: response.data.email,
        phone: response.data.phone,
        business_name: response.data.business_name,
        business_type: response.data.business_type,
        monthly_volume: response.data.monthly_volume,
      });
      
      // Track uploaded documents
      const docs = {};
      response.data.documents.forEach((doc) => {
        docs[doc.document_type] = doc;
      });
      setUploadedDocs(docs);
    } catch (err) {
      setError('Failed to load submission');
    } finally {
      setLoading(false);
    }
  };

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: value,
    }));
  };

  const handleDocumentChange = (e, docType) => {
    const file = e.target.files[0];
    if (file) {
      if (file.size > 5 * 1024 * 1024) {
        setError('File size exceeds 5 MB');
        return;
      }
      setDocuments((prev) => ({
        ...prev,
        [docType]: file,
      }));
    }
  };

  const handleSaveDraft = async (e) => {
    e.preventDefault();
    setSubmitting(true);
    setError('');

    try {
      if (isUpdate) {
        await kycAPI.updateSubmission(id, formData);
        setSuccess('Draft updated successfully');
      } else {
        const response = await kycAPI.createSubmission(formData);
        setSubmission(response.data);
        setSuccess('Draft created successfully. Now upload documents.');
      }
    } catch (err) {
      const message = err.response?.data?.error || 'Failed to save';
      setError(typeof message === 'object' ? Object.values(message)[0] : message);
    } finally {
      setSubmitting(false);
    }
  };

  const handleUploadDocument = async (docType) => {
    if (!documents[docType]) {
      setError(`Please select ${docType} file`);
      return;
    }

    setSubmitting(true);
    setError('');

    try {
      const response = await kycAPI.uploadDocument(
        submission.id,
        docType,
        documents[docType]
      );
      setUploadedDocs((prev) => ({
        ...prev,
        [docType]: response.data,
      }));
      setDocuments((prev) => ({
        ...prev,
        [docType]: null,
      }));
      setSuccess(`${docType.toUpperCase()} uploaded successfully`);
    } catch (err) {
      const message = err.response?.data?.error || 'Upload failed';
      setError(typeof message === 'object' ? Object.values(message)[0] : message);
    } finally {
      setSubmitting(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSubmitting(true);
    setError('');

    try {
      // Check if all documents are uploaded
      if (!uploadedDocs.pan || !uploadedDocs.aadhaar || !uploadedDocs.bank_statement) {
        setError('All three documents are required');
        setSubmitting(false);
        return;
      }

      await kycAPI.submitForReview(submission.id);
      setSuccess('Submission sent for review!');
      setTimeout(() => navigate('/merchant/dashboard'), 2000);
    } catch (err) {
      const message = err.response?.data?.error || 'Submission failed';
      setError(typeof message === 'object' ? Object.values(message)[0] : message);
    } finally {
      setSubmitting(false);
    }
  };

  const handleBack = () => {
    if (window.history.length > 1) {
      navigate(-1);
      return;
    }
    navigate('/merchant/dashboard');
  };

  if (loading) {
    return <div className="flex justify-center items-center h-screen">Loading...</div>;
  }

  const canSubmit =
    uploadedDocs.pan && uploadedDocs.aadhaar && uploadedDocs.bank_statement;

  return (
    <div className="max-w-4xl mx-auto p-6">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-3xl font-bold text-gray-800">
          {isUpdate ? 'Update KYC' : 'Create New KYC Submission'}
        </h1>
        <button
          type="button"
          onClick={handleBack}
          className="bg-gray-200 hover:bg-gray-300 text-gray-800 font-semibold py-2 px-4 rounded-lg transition"
        >
          Back
        </button>
      </div>

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

      <div className="bg-white rounded-lg shadow-md p-6 mb-6">
        <h2 className="text-xl font-semibold mb-4 text-gray-800">Personal Information</h2>
        <form onSubmit={handleSaveDraft} className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Full Name
              </label>
              <input
                type="text"
                name="name"
                value={formData.name}
                onChange={handleInputChange}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Email
              </label>
              <input
                type="email"
                name="email"
                value={formData.email}
                onChange={handleInputChange}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Phone
              </label>
              <input
                type="tel"
                name="phone"
                value={formData.phone}
                onChange={handleInputChange}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                required
              />
            </div>
          </div>

          <h2 className="text-xl font-semibold mb-4 mt-6 text-gray-800">Business Information</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Business Name
              </label>
              <input
                type="text"
                name="business_name"
                value={formData.business_name}
                onChange={handleInputChange}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Business Type
              </label>
              <input
                type="text"
                name="business_type"
                value={formData.business_type}
                onChange={handleInputChange}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Monthly Volume (INR)
              </label>
              <input
                type="number"
                name="monthly_volume"
                value={formData.monthly_volume}
                onChange={handleInputChange}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                required
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={submitting}
            className="mt-4 bg-blue-600 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded-lg transition disabled:opacity-50"
          >
            {submitting ? 'Saving...' : 'Save Draft'}
          </button>
        </form>
      </div>

      {submission && (
        <div className="bg-white rounded-lg shadow-md p-6">
          <h2 className="text-xl font-semibold mb-4 text-gray-800">Upload Documents</h2>
          <p className="text-sm text-gray-600 mb-4">
            All three documents are required. Accepted formats: PDF, JPG, PNG (Max 5 MB)
          </p>

          <div className="space-y-4">
            {['pan', 'aadhaar', 'bank_statement'].map((docType) => (
              <div key={docType} className="p-4 border border-gray-200 rounded-lg">
                <div className="flex items-center justify-between">
                  <div className="flex-1">
                    <h3 className="font-semibold text-gray-800 mb-2">
                      {docType === 'bank_statement' ? 'Bank Statement' : docType.toUpperCase()}
                    </h3>
                    {uploadedDocs[docType] ? (
                      <p className="text-green-600 font-semibold">✓ Uploaded</p>
                    ) : (
                      <div className="flex gap-2">
                        <input
                          type="file"
                          onChange={(e) => handleDocumentChange(e, docType)}
                          accept=".pdf,.jpg,.jpeg,.png"
                          className="text-sm text-gray-600"
                        />
                        <button
                          type="button"
                          onClick={() => handleUploadDocument(docType)}
                          disabled={!documents[docType] || submitting}
                          className="bg-green-600 hover:bg-green-700 text-white px-3 py-1 rounded text-sm transition disabled:opacity-50"
                        >
                          Upload
                        </button>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>

          <button
            onClick={handleSubmit}
            disabled={!canSubmit || submitting}
            className="mt-6 w-full bg-blue-600 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded-lg transition disabled:opacity-50"
          >
            {submitting ? 'Submitting...' : 'Submit for Review'}
          </button>
        </div>
      )}
    </div>
  );
};

export default MerchantForm;
