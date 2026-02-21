import React, { useState, useEffect, useRef } from 'react';
import './HomePage.css';

const FadeInSection = ({ children, delay = 0, direction = 'up' }) => {
    const [isVisible, setVisible] = useState(false);
    const domRef = useRef();

    useEffect(() => {
        const observer = new IntersectionObserver(
            entries => {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        setVisible(true);
                        observer.unobserve(domRef.current);
                    }
                });
            },
            { threshold: 0.15 }
        );

        if (domRef.current) {
            observer.observe(domRef.current);
        }
        return () => {
            if (domRef.current) observer.disconnect();
        };
    }, []);

    return (
        <div
            className={`fade-in-section direction-${direction} ${isVisible ? 'is-visible' : ''}`}
            ref={domRef}
            style={{ transitionDelay: `${delay}ms` }}
        >
            {children}
        </div>
    );
};

function HomePage({ onNavigate }) {
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
                            onClick={() => onNavigate('analyze')}
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

            {/* FEATURES SECTION (NO BOXES, NO GRADIENTS, JUST CLEAN FLOW) */}
            <section className="features-flow-section">

                {/* Feature 1 */}
                <div className="feature-row">
                    <FadeInSection direction="left" delay={100}>
                        <div className="feature-illustration">
                            <svg viewBox="0 0 100 100" fill="none" className="ill-svg ill-1">
                                <path d="M20 50 Q 50 20 80 50 T 20 50" fill="var(--color-accent-primary)" opacity="0.1" />
                                <circle cx="50" cy="50" r="20" stroke="var(--color-text-primary)" strokeWidth="3" strokeDasharray="5 5" opacity="0.5">
                                    <animateTransform attributeName="transform" type="rotate" from="0 50 50" to="360 50 50" dur="20s" repeatCount="indefinite" />
                                </circle>
                                <circle cx="50" cy="50" r="8" fill="var(--color-accent-primary)" />
                            </svg>
                        </div>
                    </FadeInSection>
                    <FadeInSection direction="right" delay={200}>
                        <div className="feature-text-content">
                            <h2 className="feature-heading">Premium functionality.<br />Zero subscription.</h2>
                            <p className="feature-description">
                                Everything other health apps charge you for is completely free here. Enjoy unlimited product searches and instant analysis without ever hitting a paywall.
                            </p>
                        </div>
                    </FadeInSection>
                </div>

                {/* Feature 2 */}
                <div className="feature-row reverse">
                    <FadeInSection direction="right" delay={100}>
                        <div className="feature-illustration">
                            <svg viewBox="0 0 100 100" fill="none" className="ill-svg ill-2">
                                <circle cx="50" cy="50" r="30" stroke="var(--color-accent-primary)" strokeWidth="3" opacity="0.2" />
                                <circle cx="50" cy="50" r="15" fill="var(--color-accent-primary)">
                                    <animate attributeName="r" values="15; 20; 15" dur="3s" repeatCount="indefinite" />
                                </circle>
                                <path d="M50 15 L50 5 M50 95 L50 85 M15 50 L5 50 M95 50 L85 50" stroke="var(--color-text-primary)" strokeWidth="3" opacity="0.4" strokeLinecap="round" />
                            </svg>
                        </div>
                    </FadeInSection>
                    <FadeInSection direction="left" delay={200}>
                        <div className="feature-text-content">
                            <h2 className="feature-heading">Unlimited tracking.<br />Endless searches.</h2>
                            <p className="feature-description">
                                We provide instant search, safely secured search history, and personalized recommendations—powerful features that usually cost money, given directly to you for zero cost.
                            </p>
                        </div>
                    </FadeInSection>
                </div>

                {/* Feature 3 */}
                <div className="feature-row">
                    <FadeInSection direction="left" delay={100}>
                        <div className="feature-illustration">
                            <svg viewBox="0 0 100 100" fill="none" className="ill-svg ill-3">
                                <ellipse cx="50" cy="50" rx="40" ry="15" stroke="var(--color-accent-primary)" strokeWidth="2" opacity="0.3" fill="none" transform="rotate(20 50 50)" />
                                <ellipse cx="50" cy="50" rx="40" ry="15" stroke="var(--color-text-primary)" strokeWidth="2" opacity="0.3" fill="none" transform="rotate(70 50 50)" />
                                <circle cx="50" cy="50" r="12" fill="var(--color-accent-primary)" />
                            </svg>
                        </div>
                    </FadeInSection>
                    <FadeInSection direction="right" delay={200}>
                        <div className="feature-text-content">
                            <h2 className="feature-heading">Uncompromised truth.<br />Pure transparency.</h2>
                            <p className="feature-description">
                                We translate complicated health labels into simple truths. No sponsored biases, no hidden algorithms. Know exactly how your food impacts your health before making a choice.
                            </p>
                        </div>
                    </FadeInSection>
                </div>

            </section>

            {/* ABOUT SECTION ALIGNED TO PREMIUM AESTHETIC */}
            <section className="about-embedded-section" id="about-section">
                <FadeInSection direction="up" delay={100}>
                    <div className="about-content-wrapper">
                        <div className="about-header-minimal">
                            <h2 className="feature-heading" style={{ textAlign: 'center', marginBottom: '1rem' }}>Why Ingrexa?</h2>
                            <div className="underline-accent"></div>
                        </div>
                        <div className="about-text-minimal">
                            <p className="feature-description about-lead">
                                Every time I picked up a food product in India, I found myself Googling ingredients I couldn't understand.
                                <span className="highlight-text"> What is INS 621? Is palm oil really that bad? Should I avoid this preservative?</span>
                            </p>
                            <p className="feature-description">
                                I couldn't find a good, India-centric web app that made this simple. So I built one.
                            </p>
                            <p className="feature-description about-mission">
                                Making food transparency accessible to everyone. 🇮🇳
                            </p>
                        </div>
                    </div>
                </FadeInSection>
            </section>
        </main>
    );
}

export default HomePage;
