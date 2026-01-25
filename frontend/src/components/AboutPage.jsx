import React from 'react';

function AboutPage() {
    return (
        <section className="about-page">
            <div className="about-container">
                <div className="about-hero">
                    <h1 className="about-title">Why Ingrexa?</h1>
                </div>

                <div className="about-story">
                    <p className="about-text">
                        Every time I picked up a food product in India, I found myself Googling ingredients
                        I couldn't understand. <span className="highlight">What is INS 621? Is palm oil really that bad?
                            Should I avoid this preservative?</span>
                    </p>

                    <p className="about-text">
                        I couldn't find a good, India-centric web app that made this simple.
                        So I built one.
                    </p>

                    <p className="about-text emphasis">
                        By users, for users. 🇮🇳
                    </p>

                    <p className="about-text small">
                        Upload a product image or paste a URL to get instant, clear ingredient analysis.
                        No more endless Googling.
                    </p>
                </div>
            </div>
        </section>
    );
}

export default AboutPage;
