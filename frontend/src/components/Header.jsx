import React, { useState } from 'react';

function Header({ onNavigate, currentPage }) {
  const [isMenuOpen, setIsMenuOpen] = useState(false);

  const handleNavClick = (page) => {
    setIsMenuOpen(false);
    onNavigate(page);
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
          className={`nav-link ${currentPage === 'scoring' ? 'active' : ''}`}
          onClick={(e) => { e.preventDefault(); handleNavClick('scoring'); }}
        >
          How it Works
        </a>

        <a
          href="#"
          className={`nav-link ${currentPage === 'contact' ? 'active' : ''}`}
          onClick={(e) => { e.preventDefault(); handleNavClick('contact'); }}
        >
          Contact
        </a>
      </nav>
    </header>
  );
}

export default Header;
