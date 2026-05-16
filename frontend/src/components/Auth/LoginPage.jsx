import React, { useState } from 'react';
import { motion } from 'framer-motion';
import api from '../../api';
import { useGoogleLogin } from '@react-oauth/google';
import { generateNonce } from '../../utils/nonce';

const ShieldIcon = () => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#0D1117" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round">
    <path d="M12 2L3 7v9c0 5 9 6 9 6s9-1 9-6V7l-9-5z" />
  </svg>
);

const LoginPage = ({ onNavigate, onLoginSuccess }) => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const googleLogin = useGoogleLogin({
    onSuccess: async (tokenResponse) => {
      setLoading(true); setError('');
      try {
        const nonce = generateNonce();
        const response = await api.post('/api/auth/google-login/', { access_token: tokenResponse.access_token, nonce });
        if (onLoginSuccess) onLoginSuccess(response.data.access);
        onNavigate('analyze');
      } catch (err) {
        setError(err.response?.data?.message || 'Google authentication failed.');
      } finally { setLoading(false); }
    },
    onError: () => setError('Google Authentication Failed.'),
  });

  const handleSubmit = async (e) => {
    e.preventDefault(); setLoading(true); setError('');
    try {
      const response = await api.post('/api/auth/token/', { email, password });
      if (onLoginSuccess) onLoginSuccess(response.data.access);
      onNavigate('analyze');
    } catch (err) {
      setError(err.response?.data?.detail || 'Invalid email or password.');
    } finally { setLoading(false); }
  };

  const handleDemoLogin = async () => {
    setLoading(true); setError('');
    try {
      const response = await api.post('/api/auth/token/', { email: 'demo@ingrexa.com', password: 'password123' });
      if (onLoginSuccess) onLoginSuccess(response.data.access);
      onNavigate('analyze');
    } catch (err) {
      setError(err.response?.data?.detail || 'Demo login failed.');
    } finally { setLoading(false); }
  };

  return (
    <div className="auth-page">
      <div className="auth-bg-glow" />
      <motion.div className="auth-card" initial={{ opacity: 0, scale: 0.94, y: 24 }} animate={{ opacity: 1, scale: 1, y: 0 }} transition={{ duration: 0.5, ease: [0.16, 1, 0.3, 1] }}>
        <div className="auth-logo-row">
          <div className="auth-logo-icon"><ShieldIcon /></div>
          <span className="auth-logo-text">Ingrexa</span>
        </div>
        <h1 className="auth-title">Welcome back</h1>
        <p className="auth-sub">Sign in to access your ingredient sanctuary.</p>

        {error && <motion.div className="auth-error" initial={{ opacity: 0, y: -8 }} animate={{ opacity: 1, y: 0 }}>{error}</motion.div>}

        <form className="auth-form" onSubmit={handleSubmit}>
          <div className="auth-field-wrap">
            <label className="auth-label">Email Address</label>
            <input type="email" className="auth-input" placeholder="name@company.com" value={email} onChange={e => setEmail(e.target.value)} required />
          </div>
          <div className="auth-field-wrap">
            <label className="auth-label">Password</label>
            <input type="password" className="auth-input" placeholder="••••••••" value={password} onChange={e => setPassword(e.target.value)} required />
          </div>
          <motion.button type="submit" className="auth-submit" disabled={loading} whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.98 }}>
            {loading ? 'Verifying…' : <>
              Sign in
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><path d="M5 12h14M12 5l7 7-7 7" /></svg>
            </>}
          </motion.button>
        </form>

        <div className="auth-divider"><span>OR</span></div>

        <motion.button className="auth-google" onClick={handleDemoLogin} type="button" disabled={loading} whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.98 }} style={{ background: 'var(--brand-primary)', color: '#0D1117', fontWeight: 700, marginBottom: 'var(--space-3)', border: 'none' }}>
          ✨ Demo Login (Instant Bypass)
        </motion.button>

        <motion.button className="auth-google" onClick={() => googleLogin()} type="button" disabled={loading} whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.98 }}>
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" fill="#4285F4"/>
            <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853"/>
            <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" fill="#FBBC05"/>
            <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.(87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335"/>
          </svg>
          Continue with Google
        </motion.button>

        <div className="auth-footer">
          New to Ingrexa?{' '}
          <span className="auth-link" onClick={() => onNavigate('signup')}>Create Account</span>
        </div>
      </motion.div>
    </div>
  );
};

export default LoginPage;
