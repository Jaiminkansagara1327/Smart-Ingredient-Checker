import React, { useState, useEffect } from 'react';
import api from '../../api';

function Header({ onNavigate, currentPage, user, setUser }) {
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const [isProcessingSupport, setIsProcessingSupport] = useState(false);
  const [showProfileDropdown, setShowProfileDropdown] = useState(false);

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (e) => {
      if (!e.target.closest('.profile-menu-container')) {
        setShowProfileDropdown(false);
      }
    };
    document.addEventListener('click', handleClickOutside);
    return () => document.removeEventListener('click', handleClickOutside);
  }, []);
  
  const handleLogout = () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('ingrexa_cached_user');
    setUser(null);
    onNavigate('home');
    setIsMenuOpen(false);
  };

  const handleNavClick = (page) => {
    setIsMenuOpen(false);
    onNavigate(page);
  };

  const handleSupport = async (e) => {
    e.preventDefault();
    if (isProcessingSupport) return;
    
    setIsProcessingSupport(true);
    try {
      // Step 1: Create Order in Backend
      const orderResponse = await api.post('/api/razorpay/create-order/', {
        amount: 49 // Fixed support amount: 49 INR
      });

      if (!orderResponse.data.success) {
        throw new Error(orderResponse.data.message || 'Order creation failed');
      }

      const { order_id, amount, currency, key_id } = orderResponse.data;

      // Step 2: Open Razorpay Checkout Popup
      const options = {
        key: key_id,
        amount: amount,
        currency: currency,
        name: 'Ingrexa',
        description: 'Support Independent Food Analysis',
        image: '/logo.png',
        order_id: order_id,
        handler: async function (response) {
            // Step 3: Verify Payment in Backend after success
            try {
              const verifyResponse = await api.post('/api/razorpay/verify-payment/', {
                  razorpay_order_id: response.razorpay_order_id,
                  razorpay_payment_id: response.razorpay_payment_id,
                  razorpay_signature: response.razorpay_signature,
              });
              
              if (verifyResponse.data.success) {
                  alert('Thank you for your support! Payment verified successfully.');
              } else {
                  alert('Payment verification failed. Please contact us if money was deducted.');
              }
            } catch (err) {
              console.error('Verification error:', err);
              alert('Error verifying payment. Please contact support.');
            }
        },
        prefill: {
          name: '',
          email: '',
          contact: ''
        },
        theme: {
          color: '#0d9488' // Teal accent color
        },
        modal: {
            ondismiss: function() {
                setIsProcessingSupport(false);
            }
        }
      };

      const rzp = new window.Razorpay(options);
      rzp.open();

    } catch (error) {
      console.error('Razorpay Error:', error);
      alert('Could not initiate payment. Please try again later.');
    } finally {
      setIsProcessingSupport(false);
    }
  };

  return (
    <header className="header">
      <div className="logo" onClick={() => handleNavClick('home')} style={{ cursor: 'pointer' }}>
        <img src="/logo.png" alt="Ingrexa Logo" className="logo-img" />
        <span className="logo-text">Ingrexa</span>
      </div>

      <button
        className={`mobile-menu-btn ${isMenuOpen ? 'open' : ''}`}
        onClick={() => setIsMenuOpen(!isMenuOpen)}
        aria-label="Toggle Navigation"
      >
        <span className="hamburger-line line-1"></span>
        <span className="hamburger-line line-2"></span>
        <span className="hamburger-line line-3"></span>
      </button>

      <nav className={`nav ${isMenuOpen ? 'nav-open' : ''}`}>
        <a
          href="#"
          className={`nav-link ${currentPage === 'home' ? 'active' : ''}`}
          onClick={(e) => { e.preventDefault(); handleNavClick('home'); }}
        >
          Home
        </a>

        <a
          href="#"
          className={`nav-link ${currentPage === 'analyze' ? 'active' : ''}`}
          onClick={(e) => { 
            e.preventDefault(); 
            if (user) {
              handleNavClick('analyze');
            } else {
              handleNavClick('login');
            }
          }}
        >
          Analyze
        </a>

        <a
          href="#"
          className={`nav-link ${currentPage === 'contact' ? 'active' : ''}`}
          onClick={(e) => { e.preventDefault(); handleNavClick('contact'); }}
        >
          Contact
        </a>
        
        <button
          onClick={handleSupport}
          className="nav-link btn-support"
          disabled={isProcessingSupport}
          style={{ border: 'none', cursor: 'pointer', outline: 'none' }}
        >
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
            <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l8.84-8.84 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"></path>
          </svg>
          {isProcessingSupport ? 'Connecting...' : 'Support Ingrexa'}
        </button>

        {user ? (
          <div className="profile-menu-container" style={{ position: 'relative', marginLeft: '10px' }}>
            <div className="profile-pill" onClick={() => setShowProfileDropdown(!showProfileDropdown)}>
              <span className="profile-text">
                {user.first_name || 'My Profile'}
              </span>
              <div className="profile-avatar">
                {user.first_name ? user.first_name[0].toUpperCase() : 'U'}
              </div>
            </div>

            {showProfileDropdown && (
              <div style={{
                position: 'absolute',
                top: '55px',
                right: '0',
                backgroundColor: '#ffffff',
                borderRadius: '16px',
                boxShadow: '0 10px 30px rgba(0, 0, 0, 0.08), 0 1px 3px rgba(0,0,0,0.05)',
                border: '1px solid #f1f5f9',
                width: '240px',
                zIndex: 100,
                overflow: 'hidden',
                animation: 'slideUpFade 0.2s ease-out'
              }}>
                <div style={{ padding: '16px 20px', borderBottom: '1px solid #f1f5f9', backgroundColor: '#fdfbff' }}>
                  <p style={{ margin: '0 0 4px 0', fontWeight: '800', color: '#0f172a', fontSize: '0.95rem' }}>
                    {user.first_name || 'User'}
                  </p>
                  <p style={{ margin: '0', fontSize: '0.8rem', color: '#64748b', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }} title={user.email}>
                    {user.email}
                  </p>
                </div>
                <div style={{ padding: '8px' }}>
                  <button 
                    onClick={() => { setShowProfileDropdown(false); handleNavClick('settings'); }}
                    style={{ width: '100%', display: 'flex', alignItems: 'center', gap: '10px', textAlign: 'left', padding: '10px 12px', background: 'transparent', border: 'none', cursor: 'pointer', color: '#334155', fontSize: '0.9rem', borderRadius: '8px', fontWeight: '500', transition: 'all 0.15s ease' }}
                    onMouseOver={(e) => { e.currentTarget.style.backgroundColor = '#f8fafc'; e.currentTarget.style.color = '#0f172a'; }}
                    onMouseOut={(e) => { e.currentTarget.style.backgroundColor = 'transparent'; e.currentTarget.style.color = '#334155'; }}
                  >
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="3"></circle><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"></path></svg>
                    Settings
                  </button>
                  <button 
                    onClick={() => { setShowProfileDropdown(false); handleNavClick('history'); }}
                    style={{ width: '100%', display: 'flex', alignItems: 'center', gap: '10px', textAlign: 'left', padding: '10px 12px', background: 'transparent', border: 'none', cursor: 'pointer', color: '#334155', fontSize: '0.9rem', borderRadius: '8px', fontWeight: '500', transition: 'all 0.15s ease' }}
                    onMouseOver={(e) => { e.currentTarget.style.backgroundColor = '#f8fafc'; e.currentTarget.style.color = '#0f172a'; }}
                    onMouseOut={(e) => { e.currentTarget.style.backgroundColor = 'transparent'; e.currentTarget.style.color = '#334155'; }}
                  >
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="10"></circle><polyline points="12 6 12 12 16 14"></polyline></svg>
                    History
                  </button>
                  <div style={{ borderTop: '1px solid #f1f5f9', margin: '6px 4px' }}></div>
                  <button 
                    onClick={() => { setShowProfileDropdown(false); handleLogout(); }}
                    style={{ width: '100%', display: 'flex', alignItems: 'center', gap: '10px', textAlign: 'left', padding: '10px 12px', background: 'transparent', border: 'none', cursor: 'pointer', color: '#ef4444', fontSize: '0.9rem', borderRadius: '8px', fontWeight: '600', transition: 'all 0.15s ease' }}
                    onMouseOver={(e) => { e.currentTarget.style.backgroundColor = '#fef2f2'; }}
                    onMouseOut={(e) => { e.currentTarget.style.backgroundColor = 'transparent'; }}
                  >
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"></path><polyline points="16 17 21 12 16 7"></polyline><line x1="21" y1="12" x2="9" y2="12"></line></svg>
                    Sign out
                  </button>
                </div>
              </div>
            )}
          </div>
        ) : (
          <div className="login-pill" onClick={() => handleNavClick('login')}>
            <span className="login-text">Sign in</span>
            <div className="login-avatar">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path>
                <circle cx="12" cy="7" r="4"></circle>
              </svg>
            </div>
          </div>
        )}
      </nav>
    </header>
  );
}

export default Header;
