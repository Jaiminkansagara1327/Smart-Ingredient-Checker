import React, { useState } from 'react';
import './AuthPremium.css';
import api from '../../api';
import { GoogleLogin, useGoogleLogin } from '@react-oauth/google';
import { FaEye, FaEyeSlash } from "react-icons/fa";

const LoginPage = ({ onNavigate, onLoginSuccess }) => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  // Fallback: access_token flow (useGoogleLogin)
  const googleLoginFallback = useGoogleLogin({
    onSuccess: async (tokenResponse) => {
      setLoading(true);
      setError('');
      try {
        const response = await api.post('/api/auth/google-login/', {
          access_token: tokenResponse.access_token,
        });
        if (onLoginSuccess) onLoginSuccess(response.data.access);
        onNavigate('analyze');
      } catch (err) {
        console.error('Google login (access_token flow) error:', err);
        if (!err.response) {
          setError('Cannot connect to Django backend on http://127.0.0.1:8000. Please ensure the backend is running (python manage.py runserver).');
        } else {
          setError(err.response?.data?.message || err.response?.data?.detail || 'Google authentication failed.');
        }
      } finally {
        setLoading(false);
      }
    },
    onError: (err) => {
      console.error('Google OAuth Error (access_token flow):', err);
      setError(`Google OAuth Error: ${err.error || JSON.stringify(err)}`);
    },
  });

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const response = await api.post('/api/auth/token/', {
        email,
        password
      });

      if (onLoginSuccess) {
        onLoginSuccess(response.data.access);
      }
      onNavigate('analyze');
    } catch (err) {
      console.error('Login error', err);
      const errData = err.response?.data;
      if (err.message === 'Network Error') {
        const isLocal = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1';
        setError(`Network Error: Cannot connect to the server. ${isLocal ? 'Please ensure the Django backend is running.' : 'Please check your connection and try again.'}`);
      } else if (errData?.non_field_errors) {
        setError(errData.non_field_errors[0]);
      } else if (errData?.errors?.non_field_errors) {
        setError(errData.errors.non_field_errors[0]);
      } else {
        setError(errData?.message || errData?.detail || 'Invalid email or password. Please try again.');
      }
    } finally {
      setLoading(false);
    }
  };

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
        <h1 className="auth-brand-title">Welcome back</h1>
        <p className="auth-brand-subtitle">Enter your details to access your sanctuary.</p>
      </div>

      {error && <div className="auth-error-premium">{error}</div>}

      <form className="auth-form-premium" onSubmit={handleSubmit}>
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
              placeholder="••••••••"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />

            <span
              onClick={() => setShowPassword(!showPassword)}
              style={{
                position: "absolute",
                right: "10px",
                top: "50%",
                transform: "translateY(-50%)",
                cursor: "pointer",
                fontSize: "14px"
              }}
            >
              {showPassword ? <FaEyeSlash /> : <FaEye />}
            </span>
          </div>
        </div>

        <button type="submit" className="auth-submit-btn" disabled={loading}>
          {loading ? 'Verifying...' : (
            <>
              Sign in
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

              if (onLoginSuccess) {
                onLoginSuccess(response.data.access);
              }
              onNavigate('analyze');
            } catch (err) {
              console.error('Google login error', err);
              if (!err.response) {
                setError('Cannot connect to Django backend on http://127.0.0.1:8000. Please ensure the backend is running (python manage.py runserver).');
              } else {
                setError(err.response?.data?.message || err.response?.data?.detail || 'Google authentication failed.');
              }
            } finally {
              setLoading(false);
            }
          }}
          onError={(err) => {
            console.error('Google Button Error:', err);
            setError(`Google Auth Error: ${err?.error || err?.error_description || 'Popup blocked or not authorized. Check Google Cloud Console (Authorized JS Origins must include http://localhost:3000)'}`);
          }}
        />
      </div>

      <div style={{textAlign: 'center', marginTop: '8px'}}>
        <button
          type="button"
          onClick={() => googleLoginFallback()}
          disabled={loading}
          style={{fontSize: '12px', color: '#aaa', background: 'none', border: 'none', cursor: 'pointer', textDecoration: 'underline'}}
        >
          Try alternate Google login
        </button>
      </div>

      <div className="auth-footer-premium">
        New to Ingrexa?
        <span className="auth-switch-link" onClick={() => onNavigate('signup')}>Create Account</span>
      </div>
    </div>
  );
};

export default LoginPage;
