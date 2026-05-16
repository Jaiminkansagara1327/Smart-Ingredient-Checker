import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import api, { clearAccessToken } from '../../api';
import { loadRazorpay } from '../../utils/razorpay';

const ShieldIcon = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round">
    <path d="M12 2L3 7v9c0 5 9 6 9 6s9-1 9-6V7l-9-5z" />
  </svg>
);

const HeartIcon = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
    <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l8.84 8.84 8.84-8.84a5.5 5.5 0 0 0 0-7.78z" />
  </svg>
);

const UserIcon = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
    <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" /><circle cx="12" cy="7" r="4" />
  </svg>
);

const SettingsIcon = () => (
  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
    <circle cx="12" cy="12" r="3" /><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z" />
  </svg>
);

const HistoryIcon = () => (
  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
    <circle cx="12" cy="12" r="10" /><polyline points="12 6 12 12 16 14" />
  </svg>
);

const LogoutIcon = () => (
  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
    <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" /><polyline points="16 17 21 12 16 7" /><line x1="21" y1="12" x2="9" y2="12" />
  </svg>
);

const SunIcon = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
    <circle cx="12" cy="12" r="5"/><line x1="12" y1="1" x2="12" y2="3"/><line x1="12" y1="21" x2="12" y2="23"/><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/><line x1="1" y1="12" x2="3" y2="12"/><line x1="21" y1="12" x2="23" y2="12"/><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/>
  </svg>
);

const MoonIcon = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
    <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/>
  </svg>
);

function Header({ onNavigate, currentPage, user, setUser }) {
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const [isProcessingSupport, setIsProcessingSupport] = useState(false);
  const [showProfileDropdown, setShowProfileDropdown] = useState(false);
  const [scrolled, setScrolled] = useState(false);
  const [theme, setTheme] = useState(() => localStorage.getItem('ingrexa_theme') || 'dark');

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('ingrexa_theme', theme);
  }, [theme]);

  const toggleTheme = () => {
    setTheme(prev => prev === 'dark' ? 'light' : 'dark');
  };

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 20);
    window.addEventListener('scroll', onScroll, { passive: true });
    return () => window.removeEventListener('scroll', onScroll);
  }, []);

  useEffect(() => {
    const handleClick = (e) => {
      if (!e.target.closest('.profile-menu-container')) setShowProfileDropdown(false);
    };
    document.addEventListener('click', handleClick);
    return () => document.removeEventListener('click', handleClick);
  }, []);

  useEffect(() => {
    if (isMenuOpen) document.body.style.overflow = 'hidden';
    else document.body.style.overflow = '';
    return () => { document.body.style.overflow = ''; };
  }, [isMenuOpen]);

  const handleLogout = async () => {
    try { await api.post('/api/auth/logout/'); } catch {}
    clearAccessToken(); setUser(null);
    localStorage.removeItem('ingrexa_cached_user');
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    onNavigate('home'); setIsMenuOpen(false);
  };

  const handleNavClick = (page) => { setIsMenuOpen(false); onNavigate(page); };

  const handleSupport = async (e) => {
    e.preventDefault();
    if (isProcessingSupport) return;
    setIsProcessingSupport(true);
    try {
      const orderResponse = await api.post('/api/razorpay/create-order/', { amount: 49 });
      if (!orderResponse.data.success) throw new Error(orderResponse.data.message);
      const { order_id, amount, currency, key_id } = orderResponse.data;
      const Razorpay = await loadRazorpay();
      const rzp = new Razorpay({
        key: key_id, amount, currency, name: 'Ingrexa',
        description: 'Support Independent Food Analysis', order_id,
        handler: async (response) => {
          try {
            const v = await api.post('/api/razorpay/verify-payment/', response);
            if (v.data.success) alert('Thank you! Payment verified.');
            else alert('Verification failed. Contact us if money was deducted.');
          } catch { alert('Error verifying payment. Contact support.'); }
        },
        prefill: { name: '', email: '', contact: '' },
        theme: { color: '#00FF87' },
        modal: { ondismiss: () => setIsProcessingSupport(false) },
      });
      rzp.open();
    } catch (error) {
      console.error(error); alert('Could not initiate payment. Please try again later.');
    } finally { setIsProcessingSupport(false); }
  };

  const navItems = [
    { label: 'Home', page: 'home' },
    { label: 'Analyze', page: 'analyze' },
    { label: 'Contact', page: 'contact' },
  ];

  return (
    <header className={`header ${scrolled ? 'scrolled' : ''}`}>
      {/* Logo */}
      <div className="logo" onClick={() => handleNavClick('home')}>
        <motion.div
          className="logo-icon-premium"
          whileHover={{ rotate: -6, scale: 1.08 }}
          transition={{ type: 'spring', stiffness: 400, damping: 15 }}
        >
          <ShieldIcon />
        </motion.div>
        <span className="logo-text">Ingrexa</span>
      </div>

      {/* Mobile hamburger */}
      <button
        className={`mobile-menu-btn ${isMenuOpen ? 'open' : ''}`}
        onClick={() => setIsMenuOpen(!isMenuOpen)}
        aria-label="Toggle Navigation"
      >
        <span className="hamburger-line line-1" />
        <span className="hamburger-line line-2" />
        <span className="hamburger-line line-3" />
      </button>

      {/* Nav */}
      <nav className={`nav ${isMenuOpen ? 'nav-open' : ''}`}>
        {navItems.map(({ label, page }) => (
          <a
            key={page}
            href="#"
            className={`nav-link ${currentPage === page ? 'active' : ''}`}
            onClick={(e) => {
              e.preventDefault();
              if (page === 'analyze' && !user) handleNavClick('login');
              else handleNavClick(page);
            }}
          >
            {label}
          </a>
        ))}

        {/* Theme Toggle Button */}
        <motion.button
          onClick={toggleTheme}
          className="nav-link btn-theme-toggle"
          aria-label="Toggle Theme"
          whileHover={{ scale: 1.08 }}
          whileTap={{ scale: 0.92 }}
          style={{
            background: 'var(--surface-glass)',
            border: '1px solid var(--border-subtle)',
            borderRadius: 'var(--radius-full)',
            width: 38, height: 38, display: 'flex', alignItems: 'center', justifyContent: 'center',
            color: 'var(--text-primary)', cursor: 'pointer', padding: 0
          }}
        >
          {theme === 'dark' ? <SunIcon /> : <MoonIcon />}
        </motion.button>

        <motion.button
          onClick={handleSupport}
          className="nav-link btn-support"
          disabled={isProcessingSupport}
          whileHover={{ scale: 1.03 }}
          whileTap={{ scale: 0.97 }}
        >
          <HeartIcon />
          {isProcessingSupport ? 'Connecting…' : 'Support Ingrexa'}
        </motion.button>

        {user ? (
          <div className="profile-menu-container">
            <motion.div
              className="profile-pill"
              onClick={() => setShowProfileDropdown(!showProfileDropdown)}
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
            >
              <span className="profile-text">{user.first_name || 'My Profile'}</span>
              <div className="profile-avatar">
                {user.first_name ? user.first_name[0].toUpperCase() : 'U'}
              </div>
            </motion.div>

            <AnimatePresence>
              {showProfileDropdown && (
                <motion.div
                  className="profile-dropdown"
                  initial={{ opacity: 0, y: -8, scale: 0.96 }}
                  animate={{ opacity: 1, y: 0, scale: 1 }}
                  exit={{ opacity: 0, y: -8, scale: 0.96 }}
                  transition={{ duration: 0.18, ease: [0.16, 1, 0.3, 1] }}
                >
                  <div className="profile-dropdown-header">
                    <p className="profile-dropdown-name">{user.first_name || 'User'}</p>
                    <p className="profile-dropdown-email" title={user.email}>{user.email}</p>
                  </div>
                  <div className="profile-dropdown-body">
                    <button className="profile-dropdown-item" onClick={() => { setShowProfileDropdown(false); handleNavClick('settings'); }}>
                      <SettingsIcon /> Settings
                    </button>
                    <button className="profile-dropdown-item" onClick={() => { setShowProfileDropdown(false); handleNavClick('history'); }}>
                      <HistoryIcon /> History
                    </button>
                    <div className="profile-dropdown-divider" />
                    <button className="profile-dropdown-item item-danger" onClick={() => { setShowProfileDropdown(false); handleLogout(); }}>
                      <LogoutIcon /> Sign out
                    </button>
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        ) : (
          <motion.div
            className="login-pill"
            onClick={() => handleNavClick('login')}
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
          >
            <span className="login-text">Sign in</span>
            <div className="login-avatar"><UserIcon /></div>
          </motion.div>
        )}
      </nav>
    </header>
  );
}

export default Header;
