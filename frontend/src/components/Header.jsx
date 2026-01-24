import React from 'react';

function Header({ onNavigate, currentPage }) {
  return (
    <header className="header">
      <div className="logo">
        <svg className="logo-icon" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
          <path d="M12 2L2 7L12 12L22 7L12 2Z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
          <path d="M2 17L12 22L22 17" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
          <path d="M2 12L12 17L22 12" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
        </svg>
        <span className="logo-text">FoodView</span>
      </div>
      <nav className="nav">
        <a 
          href="#" 
          className={`nav-link ${currentPage === 'analyze' ? 'active' : ''}`}
          onClick={(e) => { e.preventDefault(); onNavigate('analyze'); }}
        >
          Analyze
        </a>
        <a 
          href="#" 
          className={`nav-link ${currentPage === 'about' ? 'active' : ''}`}
          onClick={(e) => { e.preventDefault(); onNavigate('about'); }}
        >
          About
        </a>
      </nav>
    </header>
  );
}

export default Header;
