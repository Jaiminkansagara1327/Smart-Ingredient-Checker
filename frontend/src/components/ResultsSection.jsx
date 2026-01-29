import React from 'react';

function ResultsSection({ data, image, onAnalyzeNew }) {
    if (!data) return null;

    // Check if this was manual input (100% confidence or input_method = manual)
    const isManualInput = data.input_method === 'manual' ||
        (data.ocr_metadata && data.ocr_metadata.quality_score === 100);

    return (
        <section className="results-section">
            <div className="results-container-new">
                {/* User Input Ingredients */}
                {data.raw_ingredients && (() => {
                    // Smart split that respects parentheses
                    const splitIngredients = (text) => {
                        const result = [];
                        let current = '';
                        let depth = 0;
                        for (let i = 0; i < text.length; i++) {
                            const char = text[i];
                            if (char === '(') depth++;
                            if (char === ')') depth--;
                            if (char === ',' && depth === 0) {
                                if (current.trim()) result.push(current.trim());
                                current = '';
                            } else {
                                current += char;
                            }
                        }
                        if (current.trim()) result.push(current.trim());
                        return result;
                    };

                    const ingredientList = splitIngredients(data.raw_ingredients);

                    return (
                        <div className="raw-input-box" style={{
                            background: 'rgba(0, 0, 0, 0.02)',
                            padding: '1.25rem',
                            borderRadius: '0.75rem',
                            border: '1px solid var(--color-border)',
                            marginBottom: '2rem'
                        }}>
                            <span style={{
                                fontSize: '0.7rem',
                                textTransform: 'uppercase',
                                letterSpacing: '0.05em',
                                fontWeight: 700,
                                color: 'var(--color-text-tertiary)',
                                display: 'block',
                                marginBottom: '0.75rem'
                            }}>Entered Ingredients</span>
                            <div style={{
                                display: 'flex',
                                flexWrap: 'wrap',
                                gap: '0.65rem'
                            }}>
                                {ingredientList.map((ing, idx) => {
                                    // Clean up: remove leading 'and ' if it exists (case-insensitive)
                                    const cleanIng = ing.trim().replace(/^and\s+/i, '');

                                    return (
                                        <span key={idx} style={{
                                            fontSize: '0.85rem',
                                            padding: '0.35rem 0.85rem',
                                            background: '#fff',
                                            border: '1px solid var(--color-border)',
                                            borderRadius: '2rem',
                                            color: 'var(--color-text-secondary)',
                                            display: 'inline-block',
                                            boxShadow: '0 1px 2px rgba(0,0,0,0.02)'
                                        }}>
                                            {cleanIng}
                                        </span>
                                    );
                                })}
                            </div>
                        </div>
                    );
                })()}

                {/* Hero Score Section */}
                <div className="score-hero">
                    <div className="score-circle">
                        <svg className="score-ring" viewBox="0 0 120 120">
                            <circle
                                className="score-ring-bg"
                                cx="60"
                                cy="60"
                                r="52"
                            />
                            <circle
                                className="score-ring-fill"
                                cx="60"
                                cy="60"
                                r="52"
                                style={{
                                    strokeDasharray: `${(data.score / 10) * 326.7} 326.7`,
                                    stroke: data.score >= 7 ? '#10b981' : data.score >= 4 ? '#f59e0b' : '#ef4444'
                                }}
                            />
                        </svg>
                        <div className="score-content">
                            <div className="score-number">{data.score}</div>
                            <div className="score-label">out of 10</div>
                        </div>
                    </div>
                    <h1 className="product-name-hero">{data.product.name}</h1>
                    <p className="product-brand-hero">{data.product.brand}</p>

                    {/* Database Badges */}
                    {(data.product.nutriscore || data.product.nova_group) && (
                        <div className="pro-badges">
                            {data.product.nutriscore && (
                                <div className={`pro-badge nutri-score nutri-${data.product.nutriscore}`}>
                                    Nutri-Score {data.product.nutriscore.toUpperCase()}
                                </div>
                            )}
                            {data.product.nova_group && (
                                <div className={`pro-badge nova-group nova-${data.product.nova_group}`}>
                                    NOVA {data.product.nova_group}
                                </div>
                            )}
                        </div>
                    )}
                </div>

                {/* Verdict */}
                <div className="verdict-modern">
                    <p className="verdict-text-modern">{data.verdict}</p>
                </div>

                {/* Suitability Grid */}
                <div className="suitability-grid">
                    <div className="suitability-card-modern good">
                        <div className="suitability-header">
                            <span className="suitability-emoji">✓</span>
                            <h3>Good For</h3>
                        </div>
                        <p>{data.suitability.goodFor}</p>
                    </div>
                    <div className="suitability-card-modern caution">
                        <div className="suitability-header">
                            <span className="suitability-emoji">⚠</span>
                            <h3>Use Caution</h3>
                        </div>
                        <p>{data.suitability.cautionFor}</p>
                    </div>
                    <div className="suitability-card-modern avoid">
                        <div className="suitability-header">
                            <span className="suitability-emoji">✕</span>
                            <h3>Avoid If</h3>
                        </div>
                        <p>{data.suitability.avoidFor}</p>
                    </div>
                </div>

                {/* Ingredient Groups - Simplified */}
                {data.ingredientGroups && data.ingredientGroups.length > 0 && (
                    <div className="ingredients-modern">
                        <h2 className="section-title-modern">Ingredients Breakdown</h2>
                        <div className="ingredient-list-modern">
                            {data.ingredientGroups.map((group, index) => (
                                <div key={index} className="ingredient-item-modern">
                                    <h3>{group.title}</h3>
                                    <p className="ingredient-desc">{group.description}</p>
                                    {group.note && <p className="ingredient-note">{group.note}</p>}
                                </div>
                            ))}
                        </div>
                    </div>
                )}

                {/* Notable Flags */}
                {data.flags && data.flags.length > 0 && (
                    <div className="flags-modern">
                        <h2 className="section-title-modern">Notable Points</h2>
                        <div className="flags-grid">
                            {data.flags.map((flag, index) => (
                                <div key={index} className="flag-modern">
                                    <span className="flag-emoji">{flag.icon}</span>
                                    <span>{flag.text}</span>
                                </div>
                            ))}
                        </div>
                    </div>
                )}

                {/* Actions */}
                <div className="actions-modern">
                    <button className="btn-modern btn-modern-primary" onClick={onAnalyzeNew}>
                        Analyze Another Product
                    </button>
                </div>

                {/* Disclaimer */}
                <div className="disclaimer-modern">
                    <p>This analysis is for informational purposes only. Consult healthcare professionals for personalized advice.</p>
                </div>
            </div>
        </section>
    );
}

export default ResultsSection;
