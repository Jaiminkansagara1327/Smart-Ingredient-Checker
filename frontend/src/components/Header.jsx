import React, { useState } from 'react';
import api from '../api';

function Header({ onNavigate, currentPage }) {
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const [isProcessingSupport, setIsProcessingSupport] = useState(false);

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
        <span className="hamburger-line line-top"></span>
        <span className="hamburger-line line-bottom"></span>
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
          onClick={(e) => { e.preventDefault(); handleNavClick('analyze'); }}
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
          {isProcessingSupport ? 'Connecting...' : 'Support My Work ☕'}
        </button>
      </nav>
    </header>
  );
}

export default Header;
