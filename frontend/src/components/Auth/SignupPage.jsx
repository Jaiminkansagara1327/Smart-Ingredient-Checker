import React, { useState } from 'react';
import './AuthPremium.css';
import api from '../../api';

const SignupPage = ({ onNavigate, onLoginSuccess }) => {
  const [firstName, setFirstName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

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
      } else {
        setError('Failed to create account. Please try again.');
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

        <button className="auth-google-btn">
          <img src="https://www.gstatic.com/images/branding/product/1x/googleg_48dp.png" width="20" height="20" alt="google" />
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
