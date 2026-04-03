import React, { useState, useEffect } from 'react';
import './HomePage.css';

function HomePage({ onNavigate }) {
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
                                const token = localStorage.getItem('access_token');
                                if (token) {
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

            {/* AUTHENTIC FEATURE 1: NUTRITION DECODING */}
            <section className="section-container" style={{ padding: '10rem 2rem', backgroundColor: 'var(--color-bg-primary)' }}>
                <div style={{ maxWidth: '1200px', margin: '0 auto', display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '6rem', alignItems: 'center' }}>
                    <div style={{ order: 1 }}>
                        <span style={{ fontSize: '0.8rem', fontWeight: '800', letterSpacing: '0.2em', color: 'var(--color-accent-primary)', textTransform: 'uppercase', marginBottom: '1.5rem', display: 'block' }}>Clinical Intelligence</span>
                        <h2 style={{ fontSize: '3.5rem', fontWeight: '800', lineHeight: '1', color: 'var(--color-text-primary)', marginBottom: '2rem', letterSpacing: '-0.04em' }}>
                            Forensic <br/>Ingredient Analysis.
                        </h2>
                        <p style={{ fontSize: '1.25rem', color: 'var(--color-text-secondary)', lineHeight: '1.8', maxWidth: '480px', marginBottom: '3rem' }}>
                            We don't provide black-box scores. We provide **Highlighting Intelligence**. Our engine scans for thousands of banned or restricted additives, unmasking industrial food processing.
                        </p>
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
                            <div style={{ display: 'flex', gap: '1.5rem', padding: '1.5rem', backgroundColor: '#fdf2f2', borderRadius: '24px', border: '1px solid #fee2e2' }}>
                                <div style={{ fontSize: '1.5rem' }}>🚩</div>
                                <div>
                                    <h4 style={{ fontWeight: '700', color: '#991b1b' }}>Red-Flag Detection</h4>
                                    <p style={{ fontSize: '0.95rem', color: '#991b1b', opacity: 0.8 }}>Automatic detection of Palm Oil, TBHQ, and Hydrogenated fats.</p>
                                </div>
                            </div>
                            <div style={{ display: 'flex', gap: '1.5rem', padding: '1.5rem', backgroundColor: '#f0fdf4', borderRadius: '24px', border: '1px solid #dcfce7' }}>
                                <div style={{ fontSize: '1.5rem' }}>🌱</div>
                                <div>
                                    <h4 style={{ fontWeight: '700', color: '#166534' }}>Nutrient Verification</h4>
                                    <p style={{ fontSize: '0.95rem', color: '#166534', opacity: 0.8 }}>Mapping whole grains, fiber, and micronutrient density.</p>
                                </div>
                            </div>
                        </div>
                    </div>
                    <div style={{ order: 2 }}>
                         {/* Visual Representation of REAL ingredient highlighting logic */}
                         <div style={{ 
                             backgroundColor: '#faf8ff', 
                             borderRadius: '32px', 
                             padding: '2.5rem', 
                             border: '1px solid #eef0ff',
                             fontFamily: 'monospace',
                             fontSize: '1rem',
                             lineHeight: '1.8',
                             color: '#334155'
                         }}>
                             <div style={{ marginBottom: '1.5rem', borderBottom: '1px solid #eef0ff', paddingBottom: '1rem', fontFamily: 'var(--font-family)', display: 'flex', justifyContent: 'space-between' }}>
                                 <span style={{ fontWeight: '800' }}>INGREDIENTS LIST</span>
                                 <span style={{ fontSize: '0.75rem', color: '#64748b' }}>ENGINE V3.4</span>
                             </div>
                             Sugar, Wheat Flour, <span style={{ backgroundColor: '#fee2e2', color: '#dc2626', padding: '2px 6px', borderRadius: '4px', fontWeight: 'bold' }}>Palm Oil</span>, 
                             Milk Solids, <span style={{ backgroundColor: '#fee2e2', color: '#dc2626', padding: '2px 6px', borderRadius: '4px', fontWeight: 'bold' }}>E150c</span>, 
                             <span style={{ backgroundColor: '#fee2e2', color: '#dc2626', padding: '2px 6px', borderRadius: '4px', fontWeight: 'bold' }}>INS 503(ii)</span>, 
                             Salt, <span style={{ backgroundColor: '#dcfce7', color: '#16a34a', padding: '2px 6px', borderRadius: '4px', fontWeight: 'bold' }}>Natural Vanilla</span>, 
                             Lecithin, <span style={{ backgroundColor: '#fee2e2', color: '#dc2626', padding: '2px 6px', borderRadius: '4px', fontWeight: 'bold' }}>Synthethic Flavor</span>.
                         </div>
                         <p style={{ fontSize: '0.85rem', color: '#64748b', marginTop: '1.5rem', textAlign: 'center' }}>Real-time highlighting as used in our internal analyzer.</p>
                    </div>
                </div>
            </section>

            {/* AUTHENTIC FEATURE 2: TRANSPARENT DATA */}
            <section className="section-container" style={{ padding: '8rem 2rem', backgroundColor: 'var(--color-bg-secondary)' }}>
                <div style={{ maxWidth: '1200px', margin: '0 auto', textAlign: 'center' }}>
                    <div style={{ marginBottom: '6rem' }}>
                        <h2 style={{ fontSize: 'clamp(2rem, 4vw, 3rem)', fontWeight: '800', color: '#131b2e', maxWidth: '800px', margin: '0 auto', lineHeight: '1.1' }}>
                            No Black Boxes. <span style={{ color: 'var(--color-accent-primary)' }}>Just Data.</span>
                        </h2>
                        <p style={{ fontSize: '1.2rem', color: '#57657b', marginTop: '1.5rem' }}>We expose the raw data so you making the final decision.</p>
                    </div>
                    
                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '2rem', textAlign: 'left' }}>
                        <div style={{ padding: '3rem', backgroundColor: 'white', borderRadius: '32px', boxShadow: 'var(--shadow-lg)' }}>
                            <h3 style={{ fontSize: '1.25rem', fontWeight: '800', marginBottom: '1rem' }}>E-Number Library</h3>
                            <p style={{ color: '#57657b', lineHeight: '1.7' }}>Our backend classifies every EU and FSSAI approved additive, revealing which ones are gut-disruptors or allergens.</p>
                        </div>
                        <div style={{ padding: '3rem', backgroundColor: 'white', borderRadius: '32px', boxShadow: 'var(--shadow-lg)' }}>
                            <h3 style={{ fontSize: '1.25rem', fontWeight: '800', marginBottom: '1rem' }}>Indian Brand Mapping</h3>
                            <p style={{ color: '#57657b', lineHeight: '1.7' }}>Specific focus on Indian manufacturing nuances, from hidden seed oils in "healthy" namkeens to high-sugar health drinks.</p>
                        </div>
                        <div style={{ padding: '3rem', backgroundColor: 'white', borderRadius: '32px', boxShadow: 'var(--shadow-lg)' }}>
                            <h3 style={{ fontSize: '1.25rem', fontWeight: '800', marginBottom: '1rem' }}>Science-First Logic</h3>
                            <p style={{ color: '#57657b', lineHeight: '1.7' }}>Our highlighting logic is based on published metabolic research, not marketing trends or affiliate partnerships.</p>
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
