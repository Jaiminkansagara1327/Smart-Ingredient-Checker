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
                {(data.ingredients || data.raw_ingredients) && (() => {
                    // Helper to clean up ingredient text from conversational and technical noise
                    const cleanIngredientText = (text) => {
                        if (!text) return '';
                        let cleaned = text
                            // 1. Remove LaTeX/Markdown math mode and escaping
                            .replace(/\\\((.*?)\\\)/g, '$1')
                            .replace(/\\\[(.*?)\\\]/g, '$1')
                            .replace(/\s*\\%\s*/g, '%') // handle escaped %
                            .replace(/\s*\\\*\s*/g, '')  // handle escaped *
                            // 2. Remove math/footnote symbols globally
                            .replace(/[\^_{\}\*\†]/g, '');

                        // 3. Iteratively remove conversational lead-ins, slashes, and technical adjectives
                        let previous;
                        do {
                            previous = cleaned;
                            cleaned = cleaned
                                // Remove leading slashes, spacers or "or" at the start
                                .replace(/^[\s/\\|.,\-*:]+/i, '')
                                .replace(/^(it also contains|also contains|contains|ingredients include|ingredients are|and|plus|permitted|synthetic|natural|nature identical|artificial|added|contains permitted|food|or)\s*[:\-]?\s*/gi, '')
                                .trim();
                        } while (cleaned !== previous);

                        return cleaned.replace(/\.$/, ''); // Remove trailing dots
                    };

                    const splitIngredients = (text) => {
                        if (!text) return [];

                        // 1. First, check if input has newlines but NO commas
                        // This handles lists like:
                        // Ingredient 1
                        // Ingredient 2
                        if (!text.includes(',') && text.includes('\n')) {
                            return text
                                .split(/\n+/)
                                .map(ing => cleanIngredientText(ing.trim()))
                                .filter(ing => ing.length > 1);
                        }

                        let cleanedText = text.replace(/\s+/g, ' ');

                        // 2. Handle patterns like "Potato (89%) Edible Oil (10%)"
                        if (!cleanedText.includes(',') && /\)\s+[A-Z]/.test(cleanedText)) {
                            return cleanedText
                                .split(/(?<=\))\s+(?=[A-Z])/)
                                .map(ing => cleanIngredientText(ing))
                                .filter(ing => ing.length > 1);
                        }

                        // 3. Fallback to standard comma/period splitting
                        const result = [];
                        let current = '';
                        let depth = 0;
                        for (let i = 0; i < cleanedText.length; i++) {
                            const char = cleanedText[i];
                            if (char === '(') depth++;
                            if (char === ')') depth--;
                            const isComma = char === ',';
                            const isPeriodSeparator = char === '.' && depth === 0 && (i === cleanedText.length - 1 || !/\d/.test(cleanedText[i + 1]));
                            if ((isComma || isPeriodSeparator) && depth === 0) {
                                if (current.trim()) result.push(current.trim());
                                current = '';
                            } else {
                                current += char;
                            }
                        }
                        if (current.trim()) result.push(current.trim());

                        return result
                            .map(ing => cleanIngredientText(ing))
                            .filter(ing => {
                                const lower = ing.toLowerCase();
                                if (lower.length < 2) return false;
                                if (['etc', 'including', 'and', 'also', 'contains', 'ingredients'].includes(lower)) return false;
                                return true;
                            });
                    };

                    // 1. Use AI-provided array if available (most reliable)
                    // 2. Else use splitIngredients on raw text
                    const rawList = data.ingredients
                        ? data.ingredients.map(ing => cleanIngredientText(ing)).filter(i => i.length > 1)
                        : splitIngredients(data.raw_ingredients);

                    // 3. Deduplicate (case-insensitive)
                    const seen = new Set();
                    const ingredientList = rawList.filter(ing => {
                        const normalized = ing.toLowerCase().trim();
                        if (seen.has(normalized)) return false;
                        seen.add(normalized);
                        return true;
                    });

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
                                    strokeDasharray: `${(data.score / 100) * 326.7} 326.7`,
                                    stroke: data.score >= 70 ? '#10b981' : data.score >= 40 ? '#f59e0b' : '#ef4444'
                                }}
                            />
                        </svg>
                        <div className="score-content">
                            <div className="score-number">{data.score}</div>
                            <div className="score-label" style={{
                                color: data.score >= 70 ? '#059669' : data.score >= 40 ? '#d97706' : '#dc2626',
                                fontWeight: 700,
                                textTransform: 'uppercase',
                                fontSize: '0.75rem',
                                letterSpacing: '0.05em'
                            }}>
                                {data.score >= 85 ? 'Excellent' :
                                    data.score >= 70 ? 'Very Good' :
                                        data.score >= 55 ? 'Average' :
                                            data.score >= 40 ? 'Fair' : 'Junk Food'}
                            </div>
                        </div>
                    </div>
                    {data.product.name && !['Food Product', 'Detected Product'].includes(data.product.name) && (
                        <h1 className="product-name-hero">{data.product.name}</h1>
                    )}
                    {data.product.brand && !['Unknown Brand', 'Unknown'].includes(data.product.brand) && (
                        <p className="product-brand-hero">{data.product.brand}</p>
                    )}

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

                    {/* How it's calculated */}
                    <div style={{
                        marginTop: '1.5rem',
                        padding: '1rem',
                        background: 'rgba(0,0,0,0.02)',
                        borderRadius: '0.75rem',
                        textAlign: 'left',
                        fontSize: '0.85rem'
                    }}>
                        <details>
                            <summary style={{ cursor: 'pointer', fontWeight: 600, color: 'var(--color-text-secondary)' }}>
                                How is this score calculated?
                            </summary>
                            <div style={{ marginTop: '0.75rem', color: 'var(--color-text-tertiary)', lineHeight: '1.5' }}>
                                <p style={{ marginBottom: '0.5rem' }}>We start with a base of <strong>100 points</strong> and deduct for:</p>
                                <ul style={{ paddingLeft: '1.25rem' }}>
                                    <li><strong>Ultra-processing:</strong> -30 to -40 pts</li>
                                    <li><strong>Artificial Additives:</strong> -5 pts each</li>
                                    <li><strong>High Sugar/HFCS:</strong> -15 to -20 pts</li>
                                    <li><strong>Refined Oils (Palm/Veg):</strong> -10 pts</li>
                                    <li><strong>Excessive Sodium:</strong> -10 pts</li>
                                </ul>
                                <p style={{ marginTop: '0.5rem', fontSize: '0.75rem', fontStyle: 'italic' }}>
                                    *Bonus points are awarded for whole grains and zero additives.
                                </p>
                            </div>
                        </details>
                    </div>
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
                                    <p className="ingredient-desc">
                                        {group.description.split(',').map(s => {
                                            let cleaned = s.replace(/\\\((.*?)\\\)/g, '$1')
                                                .replace(/\\\[(.*?)\\\]/g, '$1')
                                                .replace(/\\%/g, '%')
                                                .replace(/\\\*/g, '')
                                                .replace(/[\^_{\}\*\†]/g, '');

                                            // Iterative prefix removal
                                            let previous;
                                            do {
                                                previous = cleaned;
                                                cleaned = cleaned
                                                    .replace(/^[\s/\\|.,\-*:]+/i, '')
                                                    .replace(/^(it also contains|also contains|contains|ingredients include|ingredients are|and|plus|permitted|synthetic|natural|nature identical|artificial|added|contains permitted|food|or)\s*[:\-]?\s*/gi, '')
                                                    .trim();
                                            } while (cleaned !== previous);

                                            return cleaned;
                                        }).filter(Boolean).join(', ')}
                                    </p>
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
                                    <span>{flag.text.replace(/\\\((.*?)\\\)/g, '$1').replace(/\\%/g, '%').replace(/\\\*/g, '').replace(/[\^_{\}\*\†]/g, '')}</span>
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
