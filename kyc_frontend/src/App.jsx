import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import ProtectedRoute from './components/ProtectedRoute';

import Login from './pages/Login';
import MerchantDashboard from './pages/MerchantDashboard';
import MerchantForm from './pages/MerchantForm';
import MerchantSubmissionDetail from './pages/MerchantSubmissionDetail';
import ReviewerDashboard from './pages/ReviewerDashboard';
import ReviewerSubmissionDetail from './pages/ReviewerSubmissionDetail';

function App() {
  return (
    <Router>
      <AuthProvider>
        <Routes>
          <Route path="/login" element={<Login />} />

          {/* Merchant Routes */}
          <Route
            path="/merchant/dashboard"
            element={
              <ProtectedRoute requiredRole="merchant">
                <MerchantDashboard />
              </ProtectedRoute>
            }
          />
          <Route
            path="/merchant/create"
            element={
              <ProtectedRoute requiredRole="merchant">
                <MerchantForm />
              </ProtectedRoute>
            }
          />
          <Route
            path="/merchant/edit/:id"
            element={
              <ProtectedRoute requiredRole="merchant">
                <MerchantForm isUpdate={true} />
              </ProtectedRoute>
            }
          />
          <Route
            path="/merchant/submission/:id"
            element={
              <ProtectedRoute requiredRole="merchant">
                <MerchantSubmissionDetail />
              </ProtectedRoute>
            }
          />

          {/* Reviewer Routes */}
          <Route
            path="/reviewer/dashboard"
            element={
              <ProtectedRoute requiredRole="reviewer">
                <ReviewerDashboard />
              </ProtectedRoute>
            }
          />
          <Route
            path="/reviewer/submission/:id"
            element={
              <ProtectedRoute requiredRole="reviewer">
                <ReviewerSubmissionDetail />
              </ProtectedRoute>
            }
          />

          {/* Default Routes */}
          <Route path="/" element={<Navigate to="/login" />} />
          <Route path="*" element={<Navigate to="/login" />} />
        </Routes>
      </AuthProvider>
    </Router>
  );
}

export default App;
