import React from 'react';

function Footer() {
  const year = new Date().getFullYear();
  return (
    <footer className="footer">
      <div className="footer-inner">
        <div className="footer-brand">
          <div className="footer-logo">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#0D1117" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round">
              <path d="M12 2L3 7v9c0 5 9 6 9 6s9-1 9-6V7l-9-5z" />
            </svg>
          </div>
          <span className="footer-name" style={{ background: 'var(--gradient-brand)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>Ingrexa</span>
          <span className="footer-text">© {year} All rights reserved.</span>
        </div>
        <div className="footer-badge">
          <span className="footer-shield">🛡️</span>
          Independent &amp; unbiased — not funded by any food company.
        </div>
      </div>
    </footer>
  );
}

export default Footer;
