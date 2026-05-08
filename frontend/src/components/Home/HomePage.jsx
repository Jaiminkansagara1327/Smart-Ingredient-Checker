import React, { useState, useEffect } from 'react';
import './HomePage.css';

function HomePage({ onNavigate, user }) {
    const [showScrollToTop, setShowScrollToTop] = useState(false);

    useEffect(() => {
        const toggleVisibility = () => {
            if (window.scrollY > 400) {
                setShowScrollToTop(true);
            } else {
                setShowScrollToTop(false);
            }
        };

        window.addEventListener('scroll', toggleVisibility);
        return () => window.removeEventListener('scroll', toggleVisibility);
    }, []);

    const scrollToTop = () => {
        window.scrollTo({
            top: 0,
            behavior: 'smooth'
        });
    };

    return (
        <main className="home-wrap-premium">
            {/* HERO SECTION */}
            <section className="hero-section-premium">
                <div className="hero-background-glow"></div>
                <div className="hero-content">
                    <h1 className="hero-title-massive">
                        <span className="title-block">EAT</span>
                        <span className="title-block text-accent">FEARLESSLY.</span>
                    </h1>
                    <p className="hero-subtitle-clean">
                        No sponsors. No bias. Just the absolute truth about what you eat.
                    </p>
                    <div className="hero-cta-wrapper">
                        <button
                            className="btn-ultra-primary"
                            onClick={() => {
                                if (user) {
                                    onNavigate('analyze');
                                } else {
                                    onNavigate('login');
                                }
                            }}
                        >
                            <span>Start Analyzing</span>
                            <div className="arrow-wrapper">
                                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                                    <line x1="5" y1="12" x2="19" y2="12"></line>
                                    <polyline points="12 5 19 12 12 19"></polyline>
                                </svg>
                            </div>
                        </button>
                    </div>
                </div>
            </section>

            {/* FEATURE STORY: CLINICAL INTELLIGENCE */}
            <section className="feature-story">
                <div className="feature-story-content">
                    <div className="feature-story-text">
                        <span className="story-label">Clinical Intelligence</span>
                        <h2 className="story-title">Forensic Ingredient Analysis.</h2>
                        <p className="story-description">
                            We don't provide black-box scores. We provide <strong>Highlighting Intelligence</strong>. Our engine scans for thousands of banned or restricted additives, unmasking industrial food processing.
                        </p>
                        <div className="story-feature-list">
                            <div className="story-feature-item danger">
                                <div className="feature-item-icon">🚩</div>
                                <div className="feature-item-text">
                                    <h4>Red-Flag Detection</h4>
                                    <p>Automatic detection of Palm Oil, TBHQ, and Hydrogenated fats.</p>
                                </div>
                            </div>
                            <div className="story-feature-item success">
                                <div className="feature-item-icon">🌱</div>
                                <div className="feature-item-text">
                                    <h4>Nutrient Verification</h4>
                                    <p>Mapping whole grains, fiber, and micronutrient density.</p>
                                </div>
                            </div>
                        </div>
                    </div>
                    <div className="feature-story-visual">
                         <div className="code-block-premium">
                             <div className="code-header">
                                 <span className="code-title">INGREDIENTS LIST</span>
                                 <span className="code-tag">ENGINE V3.4</span>
                             </div>
                             <div className="code-content">
                                Sugar, Wheat Flour, <span className="highlight-danger">Palm Oil</span>, 
                                Milk Solids, <span className="highlight-danger">E150c</span>, 
                                <span className="highlight-danger">INS 503(ii)</span>, 
                                Salt, <span className="highlight-success">Natural Vanilla</span>, 
                                Lecithin, <span className="highlight-danger">Synthethic Flavor</span>.
                             </div>
                         </div>
                         <p className="visual-caption">Real-time highlighting engine.</p>
                    </div>
                </div>
            </section>

            {/* FEATURE STORY: TRANSPARENT DATA */}
            <section className="feature-story alternate">
                <div className="feature-story-content">
                    <div className="feature-story-text">
                        <span className="story-label">Transparency First</span>
                        <h2 className="story-title">No Black Boxes. Just Data.</h2>
                        <p className="story-description">
                            We expose the raw data so you make the final decision. Our library is built on published research, not marketing trends.
                        </p>
                        <div className="data-cards-grid">
                            <div className="data-mini-card">
                                <h3>E-Number Library</h3>
                                <p>Classifies gut-disruptors and allergens using EU standards.</p>
                            </div>
                            <div className="data-mini-card">
                                <h3>Brand Mapping</h3>
                                <p>Specific focus on Indian manufacturing and hidden seed oils.</p>
                            </div>
                        </div>
                    </div>
                </div>
            </section>

            {/* SCROLL TO TOP BUTTON */}
            <button
                className={`scroll-top-btn ${showScrollToTop ? 'is-visible' : ''}`}
                onClick={scrollToTop}
                aria-label="Scroll to top"
            >
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round">
                    <polyline points="18 15 12 9 6 15"></polyline>
                </svg>
            </button>
        </main>
    );
}

export default HomePage;
