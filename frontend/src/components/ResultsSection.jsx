import React from 'react';

function ResultsSection({ data, image, onAnalyzeNew }) {
    if (!data) return null;

    const placeholderImage = 'data:image/svg+xml,%3Csvg xmlns="http://www.w3.org/2000/svg" width="200" height="200"%3E%3Crect fill="%23ebe7e0" width="200" height="200"/%3E%3Ctext fill="%2378716c" font-family="Arial" font-size="14" x="50%25" y="50%25" text-anchor="middle" dominant-baseline="middle"%3EProduct Image%3C/text%3E%3C/svg%3E';

    return (
        <section className="results-section">
            <div className="results-container">
                {/* Product Info Card */}
                <div className="card product-card">
                    <div className="card-header">
                        <h2 className="card-title">Product Information</h2>
                        <span className="badge badge-success">Detected from label</span>
                    </div>
                    <div className="product-info">
                        <div className="product-image-wrapper">
                            <img
                                src={image || placeholderImage}
                                alt="Product"
                                className="product-image"
                            />
                        </div>
                        <div className="product-details">
                            <h3 className="product-name">{data.product.name}</h3>
                            <p className="product-brand">{data.product.brand}</p>
                            <span className="product-category">{data.product.category}</span>
                        </div>
                    </div>
                </div>

                {/* Verdict Card */}
                <div className="card verdict-card">
                    <div className="verdict-icon">
                        <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                            <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                            <polyline points="22 4 12 14.01 9 11.01" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                        </svg>
                    </div>
                    <h3 className="verdict-title">Quick Verdict</h3>
                    <p className="verdict-text">{data.verdict}</p>
                </div>

                {/* Suitability Card */}
                <div className="card suitability-card">
                    <div className="card-header">
                        <h2 className="card-title">Suitability Analysis</h2>
                        <div className="suitability-score">
                            <span className="score-value">{data.score}</span>
                            <span className="score-max">/10</span>
                        </div>
                    </div>
                    <div className="suitability-list">
                        <div className="suitability-item good">
                            <div className="suitability-icon">✔</div>
                            <div className="suitability-content">
                                <strong>Good for:</strong>
                                <span>{data.suitability.goodFor}</span>
                            </div>
                        </div>
                        <div className="suitability-item caution">
                            <div className="suitability-icon">⚠️</div>
                            <div className="suitability-content">
                                <strong>Caution for:</strong>
                                <span>{data.suitability.cautionFor}</span>
                            </div>
                        </div>
                        <div className="suitability-item avoid">
                            <div className="suitability-icon">❌</div>
                            <div className="suitability-content">
                                <strong>Not ideal for:</strong>
                                <span>{data.suitability.avoidFor}</span>
                            </div>
                        </div>
                    </div>
                </div>

                {/* Ingredient Summary Card */}
                <div className="card ingredients-card">
                    <div className="card-header">
                        <h2 className="card-title">Ingredient Summary</h2>
                    </div>
                    <div className="ingredient-groups">
                        {data.ingredientGroups.map((group, index) => (
                            <div key={index} className="ingredient-group">
                                <h3 className="ingredient-group-title">{group.title}</h3>
                                <p className="ingredient-group-description">{group.description}</p>
                                <p className="ingredient-group-note">{group.note}</p>
                            </div>
                        ))}
                    </div>
                </div>

                {/* Flags Card */}
                <div className="card flags-card">
                    <div className="card-header">
                        <h2 className="card-title">Notable Flags</h2>
                    </div>
                    <div className="flags-list">
                        {data.flags.map((flag, index) => (
                            <div key={index} className="flag">
                                <span className="flag-icon">{flag.icon}</span>
                                <span>{flag.text}</span>
                            </div>
                        ))}
                    </div>
                </div>

                {/* Action Buttons */}
                <div className="action-buttons">
                    <button className="btn btn-secondary" onClick={() => alert('Compare feature coming soon!')}>
                        <svg className="btn-icon" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                            <path d="M9 11H3v10h6V11zM21 3h-6v18h6V3zM15 7H9v14h6V7z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                        </svg>
                        Compare with another product
                    </button>
                    <button className="btn btn-primary" onClick={onAnalyzeNew}>
                        <svg className="btn-icon" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                            <line x1="12" y1="5" x2="12" y2="19" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
                            <line x1="5" y1="12" x2="19" y2="12" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
                        </svg>
                        Analyze New Product
                    </button>
                </div>

                {/* Disclaimer */}
                <div className="disclaimer">
                    <svg className="disclaimer-icon" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                        <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="2" />
                        <line x1="12" y1="16" x2="12" y2="12" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
                        <circle cx="12" cy="8" r="0.5" fill="currentColor" stroke="currentColor" />
                    </svg>
                    <p>Informational analysis based on ingredient data. Consult healthcare professionals for personalized advice.</p>
                </div>
            </div>
        </section>
    );
}

export default ResultsSection;
