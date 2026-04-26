import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add token to requests
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Token ${token}`;
  }
  return config;
});

// Handle responses
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export const authAPI = {
  login: (username, password) =>
    api.post('/auth/login/', { username, password }),
  logout: () => api.post('/auth/logout/'),
  getCurrentUser: () => api.get('/users/me/'),
};

export const kycAPI = {
  // Get all submissions (merchant sees only theirs, reviewer sees all)
  getSubmissions: () => api.get('/kyc/'),
  
  // Get merchant's own submissions
  getMySubmissions: () => api.get('/kyc/my_submissions/'),
  
  // Create new submission (draft)
  createSubmission: (data) => api.post('/kyc/', data),
  
  // Get submission details
  getSubmission: (id) => api.get(`/kyc/${id}/`),
  
  // Update submission
  updateSubmission: (id, data) => api.patch(`/kyc/${id}/`, data),
  
  // Upload document
  uploadDocument: (id, documentType, file) => {
    const formData = new FormData();
    formData.append('document_type', documentType);
    formData.append('file', file);
    return api.post(`/kyc/${id}/upload_document/`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },
  
  // Submit for review
  submitForReview: (id) => api.post(`/kyc/${id}/submit/`),
  
  // Change status (reviewer only)
  changeStatus: (id, newStatus, reviewerNotes = '') =>
    api.post(`/kyc/${id}/change_status/`, {
      new_status: newStatus,
      reviewer_notes: reviewerNotes,
    }),
  
  // Get queue (reviewer only)
  getQueue: (params = {}) => api.get('/kyc/queue/', { params }),
};

export const notificationAPI = {
  getNotifications: (params = {}) => api.get('/notifications/', { params }),
  getUnreadCount: () => api.get('/notifications/unread_count/'),
  markAllRead: () => api.post('/notifications/mark_all_read/'),
  markRead: (id) => api.post(`/notifications/${id}/mark_read/`),
};

export default api;
