import React, { useState, useEffect } from 'react';
import './AuthPremium.css';
import './VerifyEmail.css'; // Reuse success animation styles
import api from '../../api';
import { useGoogleLogin } from '@react-oauth/google';
import { generateNonce } from '../../utils/nonce';

const SignupPage = ({ onNavigate, onLoginSuccess }) => {
  const [step, setStep] = useState('form'); // 'form' | 'otp' | 'success'
  const [timer, setTimer] = useState(0);
  const [firstName, setFirstName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [otp, setOtp] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [exiting, setExiting] = useState(false);

  const googleLogin = useGoogleLogin({
    onSuccess: async (tokenResponse) => {
      setLoading(true);
      setError('');
      try {
        const nonce = generateNonce();
        const response = await api.post('/api/auth/google-login/', {
          access_token: tokenResponse.access_token,
          nonce,
        });

        if (onLoginSuccess) onLoginSuccess(response.data.access);
        onNavigate('analyze');
      } catch (err) {
        setError(err.response?.data?.message || 'Google authentication failed.');
      } finally {
        setLoading(false);
      }
    },
    onError: () => setError('Google Authentication Failed.')
  });

  useEffect(() => {
    let interval = null;
    if (step === 'otp' && timer > 0) {
      interval = setInterval(() => setTimer((t) => t - 1), 1000);
    } else if (timer === 0 && interval) {
      clearInterval(interval);
    }
    return () => clearInterval(interval);
  }, [step, timer]);

  const handleRegisterSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      await api.post('/api/auth/register/', { email, password, name: firstName });
      setStep('otp');
      setTimer(60);
    } catch (err) {
      const errData = err.response?.data;
      if (err.message === 'Network Error') {
        setError('Network Error. Please check your connection.');
      } else if (errData && errData.errors) {
        setError(Object.values(errData.errors).flat().join(' '));
      } else {
        setError(err.response?.data?.message || 'Failed to create account.');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleOtpSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const res = await api.post('/api/auth/verify-email/', { email, code: otp });
      setStep('success');
      
      // Auto-login and redirect after 1.5s success animation
      setTimeout(() => {
        setExiting(true);
        setTimeout(() => {
          if (onLoginSuccess) onLoginSuccess(res.data.access);
          onNavigate('analyze');
        }, 600);
      }, 1500);

    } catch (err) {
      setError(err.response?.data?.message || 'Invalid verification code.');
    } finally {
      setLoading(false);
    }
  };

  const handleResendOtp = async () => {
    setTimer(60); // Optimistic UI update
    setError('');
    try {
      await api.post('/api/auth/resend-otp/', { email });
    } catch (err) {
      setError(err.response?.data?.message || 'Failed to resend code.');
      setTimer(0);
    }
  };

  if (step === 'success') {
    return (
        <div className="verify-card verify-card--success" style={{ margin: 'auto' }}>
          <div className="verify-state verify-state--success">
            <div className="verify-check-wrap">
              <svg className="verify-check-svg" viewBox="0 0 52 52">
                <circle className="verify-check-circle" cx="26" cy="26" r="25" fill="none" />
                <path className="verify-check-mark" fill="none" d="M14 27l8 8 16-16" />
              </svg>
            </div>
            <h1 className="verify-title">Email verified!</h1>
            <p className="verify-subtitle">You're all set. Logging you in automatically…</p>
          </div>
        </div>
    );
  }

  if (step === 'otp') {
    return (
        <div className="auth-card-premium">
          <button className="auth-close-btn" onClick={() => onNavigate('home')} aria-label="Close">
             <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>
          </button>
          <div className="auth-brand-header">
            <div className="auth-brand-logo">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round">
                <path d="M12 2L3 7v9c0 5 9 6 9 6s9-1 9-6V7l-9-5z"></path>
              </svg>
            </div>
            <h1 className="auth-brand-title">Check Your Email</h1>
            <p className="auth-brand-subtitle">We sent a 6-digit code to <strong>{email}</strong>.</p>
          </div>

          {error && <div className="auth-error-premium">{error}</div>}

          <form className="auth-form-premium" onSubmit={handleOtpSubmit}>
            <div className="auth-input-wrapper">
              <label className="auth-label-premium">Verification Code</label>
              <input 
                type="text" 
                className="auth-field-premium" 
                placeholder="000000"
                value={otp}
                onChange={(e) => setOtp(e.target.value)}
                required
                maxLength={6}
                style={{ letterSpacing: '8px', textAlign: 'center', fontSize: '1.5rem', fontWeight: 'bold' }}
              />
            </div>
            <button type="submit" className="auth-submit-btn" disabled={loading}>
              {loading ? 'Verifying...' : 'Verify & Continue'}
            </button>
          </form>
          <div className="auth-footer-premium" style={{ marginTop: '20px', display: 'flex', justifyContent: 'space-between' }}>
             <span className="auth-switch-link" onClick={() => setStep('form')} style={{ marginLeft: 0 }}>Change email</span>
             {timer > 0 ? (
               <span style={{ color: '#94a3b8', fontSize: '0.85rem', fontWeight: 600 }}>Resend in {timer}s</span>
             ) : (
               <span className="auth-switch-link" onClick={handleResendOtp} style={{ marginLeft: 0 }}>Resend code</span>
             )}
          </div>
        </div>
    );
  }

  return (
      <div className="auth-card-premium">
        <button className="auth-close-btn" onClick={() => onNavigate('home')} aria-label="Close">
           <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>
        </button>
        <div className="auth-brand-header">
          <div className="auth-brand-logo">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round">
              <path d="M12 2L3 7v9c0 5 9 6 9 6s9-1 9-6V7l-9-5z"></path>
            </svg>
          </div>
          <h1 className="auth-brand-title">Create Account</h1>
          <p className="auth-brand-subtitle">Start your journey toward nutritional truth.</p>
        </div>

        {error && <div className="auth-error-premium">{error}</div>}

        <form className="auth-form-premium" onSubmit={handleRegisterSubmit}>
          <div className="auth-input-wrapper">
            <label className="auth-label-premium">Full Name</label>
            <input 
              type="text" 
              className="auth-field-premium" 
              placeholder="John Doe"
              value={firstName}
              onChange={(e) => setFirstName(e.target.value)}
              required
            />
          </div>
          <div className="auth-input-wrapper">
            <label className="auth-label-premium">Email Address</label>
            <input 
              type="email" 
              className="auth-field-premium" 
              placeholder="name@company.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />
          </div>
          <div className="auth-input-wrapper">
            <label className="auth-label-premium">Password</label>
            <input 
              type="password" 
              className="auth-field-premium" 
              placeholder="Min. 8 characters"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              minLength={8}
            />
          </div>
          <button type="submit" className="auth-submit-btn" disabled={loading}>
            {loading ? 'Creating...' : 'Get Started'}
          </button>
        </form>
        <div className="auth-social-divider">
          <span>OR</span>
        </div>
        <button className="auth-google-btn" onClick={() => googleLogin()} type="button" disabled={loading}>
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" fill="#4285F4"/>
            <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853"/>
            <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" fill="#FBBC05"/>
            <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335"/>
          </svg>
          Join with Google
        </button>
        <div className="auth-footer-premium">
          Already have an account? <span className="auth-switch-link" onClick={() => onNavigate('login')}>Sign in</span>
        </div>
      </div>
  );
};

export default SignupPage;