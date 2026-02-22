import React from 'react';

function Header({ onNavigate, currentPage }) {
  return (
    <header className="header">
      <div className="logo" onClick={() => onNavigate('home')} style={{ cursor: 'pointer' }}>
        <img src="/logo.png" alt="Ingrexa Logo" className="logo-img" />
        <span className="logo-text">Ingrexa</span>
      </div>
      <nav className="nav">
        <a
          href="#"
          className={`nav-link ${currentPage === 'home' ? 'active' : ''}`}
          onClick={(e) => { e.preventDefault(); onNavigate('home'); }}
        >
          Home
        </a>
        <a
          href="#"
          className={`nav-link ${currentPage === 'analyze' ? 'active' : ''}`}
          onClick={(e) => { e.preventDefault(); onNavigate('analyze'); }}
        >
          Analyze
        </a>
        <a
          href="#"
          className={`nav-link ${currentPage === 'scoring' ? 'active' : ''}`}
          onClick={(e) => { e.preventDefault(); onNavigate('scoring'); }}
        >
          How it Works
        </a>

        <a
          href="#"
          className={`nav-link ${currentPage === 'contact' ? 'active' : ''}`}
          onClick={(e) => { e.preventDefault(); onNavigate('contact'); }}
        >
          Contact
        </a>
      </nav>
    </header>
  );
}

export default Header;
