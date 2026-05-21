import React, { useState, useEffect, useRef } from 'react';
import './VerifyEmail.css';
import api from '../../api';

const VerifyEmailPage = ({ onNavigate }) => {
  const [status, setStatus] = useState('verifying'); // verifying | success | error
  const [message, setMessage] = useState('');
  const [progress, setProgress] = useState(0);
  const [exiting, setExiting] = useState(false);
  const progressRef = useRef(null);
  const REDIRECT_DELAY = 1500; // ms before redirect

  useEffect(() => {
    const token = window.location.pathname.split('/verify-email/')[1]?.replace(/\/$/, '');

    if (!token) {
      setStatus('error');
      setMessage('This verification link is invalid or has expired.');
      return;
    }

    api.get(`/api/auth/verify-email/${token}/`)
      .then(res => {
        setStatus('success');
        setMessage(res.data.message);


        // Fade-out then navigate
        setTimeout(() => {
          setExiting(true);
          setTimeout(() => {
            onNavigate('login');
          }, 600);
        }, REDIRECT_DELAY);
      })
      .catch(err => {
        setStatus('error');
        setMessage(err.response?.data?.message || 'We could not verify your email. The link may have expired.');
      });

    return () => {
      if (progressRef.current) clearInterval(progressRef.current);
    };
  }, []);

  return (
    <div className={`verify-page${exiting ? ' verify-page--exit' : ''}`}>
      {/* Animated background blobs */}
      <div className="verify-blob verify-blob--1" />
      <div className="verify-blob verify-blob--2" />

      <div className={`verify-card${status === 'success' ? ' verify-card--success' : ''}${status === 'error' ? ' verify-card--error' : ''}`}>

        {/* ── VERIFYING ── */}
        {status === 'verifying' && (
          <div className="verify-state verify-state--verifying">
            <div className="verify-spinner">
              <svg viewBox="0 0 50 50" className="verify-spinner-svg">
                <circle cx="25" cy="25" r="20" fill="none" strokeWidth="4" className="verify-spinner-track" />
                <circle cx="25" cy="25" r="20" fill="none" strokeWidth="4" className="verify-spinner-arc" />
              </svg>
            </div>
            <h1 className="verify-title">Verifying your email</h1>
            <p className="verify-subtitle">Just a moment, we're confirming your address…</p>
          </div>
        )}

        {/* ── SUCCESS ── */}
        {status === 'success' && (
          <div className="verify-state verify-state--success">
            {/* Animated check circle */}
            <div className="verify-check-wrap">
              <svg className="verify-check-svg" viewBox="0 0 52 52">
                <circle className="verify-check-circle" cx="26" cy="26" r="25" fill="none" />
                <path className="verify-check-mark" fill="none" d="M14 27l8 8 16-16" />
              </svg>
            </div>

            <h1 className="verify-title">Email verified!</h1>
            <p className="verify-subtitle">You're all set. Redirecting you to sign in…</p>


          </div>
        )}

        {/* ── ERROR ── */}
        {status === 'error' && (
          <div className="verify-state verify-state--error">
            <div className="verify-error-icon">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                <circle cx="12" cy="12" r="10" />
                <line x1="12" y1="8" x2="12" y2="12" />
                <line x1="12" y1="16" x2="12.01" y2="16" />
              </svg>
            </div>

            <h1 className="verify-title">Verification failed</h1>
            <p className="verify-subtitle">{message}</p>

            <button className="verify-btn" onClick={() => onNavigate('signup')}>
              Back to sign up
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                <line x1="5" y1="12" x2="19" y2="12" />
                <polyline points="12 5 19 12 12 19" />
              </svg>
            </button>
          </div>
        )}

      </div>
    </div>
  );
};

export default VerifyEmailPage;