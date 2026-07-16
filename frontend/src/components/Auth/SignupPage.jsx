import React, { useState } from 'react';
import './AuthPremium.css';
import api from '../../api';
import { GoogleLogin } from '@react-oauth/google';
import { FaEye, FaEyeSlash } from "react-icons/fa";

const SignupPage = ({ onNavigate, onLoginSuccess }) => {
  const [firstName, setFirstName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);

  const handleRegisterSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const res = await api.post('/api/auth/register/', { email, password, name: firstName });
      // Auto-login: server returns access token immediately on registration
      if (onLoginSuccess) onLoginSuccess(res.data.access);
      onNavigate('analyze');
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

  return (
    <div className="auth-card-premium">
      <button className="auth-close-btn" onClick={() => onNavigate('home')} aria-label="Close">
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
          <line x1="18" y1="6" x2="6" y2="18"></line>
          <line x1="6" y1="6" x2="18" y2="18"></line>
        </svg>
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

          <div style={{ position: "relative" }}>
            <input
              type={showPassword ? "text" : "password"}
              className="auth-field-premium"
              placeholder="Min. 8 characters"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              minLength={8}
            />

            <span
              onClick={() => setShowPassword(!showPassword)}
              style={{
                position: "absolute",
                right: "10px",
                top: "50%",
                transform: "translateY(-50%)",
                cursor: "pointer"
              }}
            >
              {showPassword ? <FaEyeSlash /> : <FaEye />}
            </span>
          </div>
        </div>
        <button type="submit" className="auth-submit-btn" disabled={loading}>
          {loading ? 'Creating Account...' : (
            <>
              Get Started
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                <line x1="5" y1="12" x2="19" y2="12"></line>
                <polyline points="12 5 19 12 12 19"></polyline>
              </svg>
            </>
          )}
        </button>
      </form>

      <div className="auth-social-divider" style={{marginTop: "20px", marginBottom: "20px"}}>
        <span>OR</span>
      </div>

      <div style={{display: 'flex', justifyContent: 'center'}}>
        <GoogleLogin
          onSuccess={async (credentialResponse) => {
            setLoading(true);
            setError('');
            try {
              const response = await api.post('/api/auth/google-login/', {
                credential: credentialResponse.credential,
              });
              if (onLoginSuccess) onLoginSuccess(response.data.access);
              onNavigate('analyze');
            } catch (err) {
              setError(err.response?.data?.message || 'Google authentication failed.');
            } finally {
              setLoading(false);
            }
          }}
          onError={() => {
            setError('Google Authentication Failed.');
          }}
          useOneTap
          text="signup_with"
        />
      </div>

      <div className="auth-footer-premium">
        Already have an account? <span className="auth-switch-link" onClick={() => onNavigate('login')}>Sign in</span>
      </div>
    </div>
  );
};

export default SignupPage;