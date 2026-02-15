import React from 'react';

function HomePage({ onNavigate }) {
    return (
        <section className="home-page">
            <div className="home-container">
                <div className="home-hero">
                    <h1 className="home-title">
                        Know What You Eat
                    </h1>
                    <p className="home-subtitle">
                        Understand food ingredients and make informed choices about your health.
                    </p>

                    <button
                        className="home-cta-button"
                        onClick={() => onNavigate('analyze')}
                    >
                        Start Analyzing
                    </button>
                </div>
            </div>
        </section>
    );
}

export default HomePage;
