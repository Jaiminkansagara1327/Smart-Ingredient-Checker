import React, { useState, useEffect } from 'react';
import './AuthPremium.css';
import api from '../../api';

const VerifyEmailPage = ({ onNavigate }) => {
  const [status, setStatus] = useState('verifying');
  const [message, setMessage] = useState('');

  useEffect(() => {
    const token = window.location.pathname.split('/verify-email/')[1]?.replace(/\/$/, '');

    if (!token) {
      setStatus('error');
      setMessage('Invalid verification link.');
      return;
    }

    api.get(`/api/auth/verify-email/${token}/`)
      .then(res => {
        setStatus('success');
        setMessage(res.data.message);
      })
      .catch(err => {
        setStatus('error');
        setMessage(err.response?.data?.message || 'Verification failed.');
      });
  }, []);

  const handleNavigate = (page) => {
    window.history.pushState({}, '', '/');
    onNavigate(page);
  };

  return (
    <div className="auth-page-premium">
      <div className="auth-bg-accent"></div>
      <div className="auth-card-premium">
        <div className="auth-brand-header">
          <div className="auth-brand-logo">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round">
              <path d="M12 2L3 7v9c0 5 9 6 9 6s9-1 9-6V7l-9-5z"></path>
            </svg>
          </div>
          {status === 'verifying' && <h1 className="auth-brand-title">Verifying your email...</h1>}
          {status === 'success' && (
            <>
              <h1 className="auth-brand-title">Email Verified ✓</h1>
              <p className="auth-brand-subtitle">{message}</p>
            </>
          )}
          {status === 'error' && (
            <>
              <h1 className="auth-brand-title">Verification Failed</h1>
              <p className="auth-brand-subtitle">{message}</p>
            </>
          )}
        </div>
        {status === 'success' && (
          <button className="auth-submit-btn" onClick={() => handleNavigate('login')}>
            Go to Login
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
              <line x1="5" y1="12" x2="19" y2="12"></line>
              <polyline points="12 5 19 12 12 19"></polyline>
            </svg>
          </button>
        )}
        {status === 'error' && (
          <button className="auth-submit-btn" onClick={() => handleNavigate('signup')}>
            Back to Sign Up
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
              <line x1="5" y1="12" x2="19" y2="12"></line>
              <polyline points="12 5 19 12 12 19"></polyline>
            </svg>
          </button>
        )}
      </div>
    </div>
  );
};

export default VerifyEmailPage;