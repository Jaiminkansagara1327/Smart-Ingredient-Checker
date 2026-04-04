import React, { useState } from 'react';
import './AuthPremium.css';
import api from '../../api';
import { useGoogleLogin } from '@react-oauth/google';

const SignupPage = ({ onNavigate, onLoginSuccess }) => {
  const [firstName, setFirstName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const googleLogin = useGoogleLogin({
    onSuccess: async (tokenResponse) => {
      setLoading(true);
      setError('');
      try {
        const response = await api.post('/api/auth/google-login/', {
          access_token: tokenResponse.access_token
        });

        localStorage.setItem('access_token', response.data.access);
        localStorage.setItem('refresh_token', response.data.refresh);
        localStorage.removeItem('ingrexa_scan_history'); 
        
        if (onLoginSuccess) {
          onLoginSuccess(response.data);
        }
        onNavigate('analyze');
      } catch (err) {
        console.error('Google login error', err);
        setError(err.response?.data?.message || 'Google authentication failed.');
      } finally {
        setLoading(false);
      }
    },
    onError: () => setError('Google Authentication Failed.')
  });

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      await api.post('/api/auth/register/', {
        email,
        password,
        name: firstName
      });

      const response = await api.post('/api/auth/token/', {
        email,
        password
      });

      localStorage.setItem('access_token', response.data.access);
      localStorage.setItem('refresh_token', response.data.refresh);
      localStorage.removeItem('ingrexa_scan_history'); 
      
      if (onLoginSuccess) {
        onLoginSuccess(response.data);
      }
      onNavigate('analyze');
    } catch (err) {
      console.error('Registration error', err);
      const errData = err.response?.data;
      if (errData && errData.errors) {
        const messages = Object.values(errData.errors).flat().join(' ');
        setError(messages);
      } else if (err.message === 'Network Error') {
        setError('Network Error: Cannot connect to the server. Please check if the backend is running.');
      } else {
        setError(err.response?.data?.message || 'Failed to create account. Server returned an error (500). Please check your backend migrations.');
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-page-premium">
      <div className="auth-bg-accent"></div>
      
      <div className="auth-card-premium">
        <div className="auth-brand-header">
          <div className="auth-brand-logo">IL</div>
          <h1 className="auth-brand-title">Create Account</h1>
          <p className="auth-brand-subtitle">Start your journey toward nutritional truth.</p>
        </div>

        {error && <div className="auth-error-premium">{error}</div>}

        <form className="auth-form-premium" onSubmit={handleSubmit}>
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
            {loading ? 'Creating...' : (
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
        <div className="auth-social-divider">
          <span>OR</span>
        </div>

        <button 
          className="auth-google-btn" 
          onClick={() => googleLogin()}
          type="button"
          disabled={loading}
        >
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" fill="#4285F4"/>
            <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853"/>
            <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" fill="#FBBC05"/>
            <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335"/>
          </svg>
          Join with Google
        </button>

        <div className="auth-footer-premium">
          Already have an account? 
          <span className="auth-switch-link" onClick={() => onNavigate('login')}>Sign in</span>
        </div>
      </div>
    </div>
  );
};

export default SignupPage;
