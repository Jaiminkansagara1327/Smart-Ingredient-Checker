import React from 'react';

function ResultsSection({ data, image, onAnalyzeNew }) {
    if (!data) return null;

    return (
        <section className="results-section">
            <div className="results-container-new" style={{ maxWidth: '800px', margin: '0 auto' }}>

                {/* 1. Hero Score Section - Premium & Minimalist */}
                <div className="score-hero" style={{ textAlign: 'center', padding: '3rem 0 2rem' }}>

                    {/* Numeric Score */}
                    <div className="score-circle-container" style={{ position: 'relative', marginBottom: '1.5rem' }}>
                        <h1 style={{
                            fontSize: '6rem',
                            fontWeight: '300',
                            lineHeight: '1',
                            color: 'var(--color-text-primary)',
                            fontFeatureSettings: '"tnum"',
                            fontVariantNumeric: 'tabular-nums',
                            letterSpacing: '-0.05em'
                        }}>
                            {data.score}
                        </h1>
                        <span style={{
                            fontSize: '1rem',
                            textTransform: 'uppercase',
                            letterSpacing: '0.2em',
                            color: 'var(--color-text-tertiary)',
                            display: 'block',
                            marginTop: '0.5rem',
                            fontWeight: 500
                        }}>
                            Health Score
                        </span>
                    </div>

                    {/* Sleek Progress Bar */}
                    <div className="score-bar-wrapper" style={{
                        height: '6px',
                        background: 'rgba(0,0,0,0.05)',
                        borderRadius: '3px',
                        maxWidth: '300px',
                        margin: '0 auto 1.5rem',
                        overflow: 'hidden'
                    }}>
                        <div
                            className="score-bar-fill"
                            style={{
                                width: `${data.score}%`,
                                height: '100%',
                                backgroundColor: data.score >= 80 ? '#10b981' :
                                    data.score >= 50 ? '#f59e0b' : '#ef4444',
                                borderRadius: '3px',
                                transition: 'width 1s cubic-bezier(0.4, 0, 0.2, 1)'
                            }}
                        />
                    </div>

                    {/* Minimal Text Verdict (No Emojis) */}
                    <div className="score-label" style={{
                        color: data.score >= 80 ? '#059669' : data.score >= 50 ? '#d97706' : '#dc2626',
                        fontWeight: 600,
                        fontSize: '1.1rem',
                        letterSpacing: '0.05em'
                    }}>
                        {data.score >= 80 ? 'Excellent' :
                            data.score >= 60 ? 'Good' :
                                data.score >= 40 ? 'Average' : 'Poor Quality'}
                    </div>
                </div>

                {/* Product Name */}
                {(data.product.name || data.product.brand) && (
                    <div style={{ textAlign: 'center', marginBottom: '3rem' }}>
                        {data.product.name && !['Food Product', 'Detected Product'].includes(data.product.name) && (
                            <h2 style={{ fontSize: '1.5rem', fontWeight: 600, marginBottom: '0.5rem', color: 'var(--color-text-primary)' }}>{data.product.name}</h2>
                        )}
                        {data.product.brand && !['Unknown Brand', 'Unknown'].includes(data.product.brand) && (
                            <p style={{ color: 'var(--color-text-tertiary)', fontSize: '0.9rem' }}>{data.product.brand}</p>
                        )}
                    </div>
                )}

                {/* Verdict / Analysis Text */}
                <div className="verdict-modern" style={{
                    textAlign: 'center',
                    fontSize: '1.1rem',
                    lineHeight: '1.6',
                    color: 'var(--color-text-secondary)',
                    maxWidth: '600px',
                    margin: '0 auto 2rem',
                    fontWeight: 400
                }}>
                    {data.verdict}
                </div>

                {/* VISIBLE Ingredient List (Restored & Cleaned) */}
                {(data.ingredients || data.raw_ingredients) && (
                    <div style={{
                        margin: '0 auto 4rem',
                        maxWidth: '700px',
                        textAlign: 'center'
                    }}>
                        <p style={{
                            fontSize: '0.7rem',
                            textTransform: 'uppercase',
                            letterSpacing: '0.1em',
                            color: 'var(--color-text-tertiary)',
                            marginBottom: '1rem',
                            fontWeight: 600
                        }}>
                            Ingredients Analyzed
                        </p>
                        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem', justifyContent: 'center' }}>
                            {(data.ingredients || (data.raw_ingredients ? data.raw_ingredients.split(',') : [])).map((ing, idx) => {
                                // Basic cleaning for display
                                const cleanIng = ing.replace(/[\(\)\[\]]/g, '').trim();
                                if (!cleanIng || cleanIng.length < 2) return null;
                                return (
                                    <span key={idx} style={{
                                        fontSize: '0.85rem',
                                        padding: '0.35rem 0.85rem',
                                        background: 'var(--color-bg-secondary)',
                                        border: '1px solid var(--color-border)',
                                        borderRadius: '100px',
                                        color: 'var(--color-text-secondary)'
                                    }}>
                                        {cleanIng}
                                    </span>
                                );
                            })}
                        </div>
                    </div>
                )}

                {/* Ingredient Breakdown List (Detailed Analysis) */}
                {data.ingredientGroups && data.ingredientGroups.length > 0 && (
                    <div className="ingredients-modern" style={{ marginTop: '2rem' }}>
                        <p style={{
                            textAlign: 'center',
                            fontSize: '0.7rem',
                            textTransform: 'uppercase',
                            letterSpacing: '0.1em',
                            color: 'var(--color-text-tertiary)',
                            marginBottom: '2rem',
                            fontWeight: 600
                        }}>
                            Detailed Breakdown
                        </p>
                        <div className="ingredient-list-modern">
                            {data.ingredientGroups.map((group, index) => (
                                <div key={index} className="ingredient-item-modern" style={{
                                    marginBottom: '2rem',
                                    borderLeft: `2px solid ${group.title.includes('Quality') ? '#ef4444' : group.title.includes('Processing') ? '#f59e0b' : '#3b82f6'}`,
                                    paddingLeft: '1.5rem'
                                }}>
                                    <h3 style={{
                                        fontSize: '0.9rem',
                                        textTransform: 'uppercase',
                                        letterSpacing: '0.05em',
                                        color: 'var(--color-text-tertiary)',
                                        marginBottom: '0.5rem',
                                        fontWeight: 600
                                    }}>
                                        {group.title}
                                    </h3>
                                    <p className="ingredient-desc" style={{
                                        fontSize: '1rem',
                                        color: 'var(--color-text-primary)',
                                        lineHeight: '1.5'
                                    }}>
                                        {group.description.split(',').map(s => s.trim()).filter(Boolean).join(', ')}
                                    </p>
                                    {group.note && (
                                        <p className="ingredient-note" style={{
                                            fontSize: '0.85rem',
                                            color: 'var(--color-text-tertiary)',
                                            marginTop: '0.25rem',
                                            fontStyle: 'italic'
                                        }}>
                                            {group.note}
                                        </p>
                                    )}
                                </div>
                            ))}
                        </div>
                    </div>
                )}

                {/* Flags (Clean Grid) */}
                {data.flags && data.flags.length > 0 && (
                    <div className="flags-modern" style={{ marginTop: '2rem' }}>
                        <div className="flags-grid" style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1rem' }}>
                            {data.flags.map((flag, index) => (
                                <div key={index} className="flag-modern" style={{
                                    padding: '1rem',
                                    background: 'var(--color-bg-tertiary)',
                                    borderRadius: '8px',
                                    fontSize: '0.9rem',
                                    color: 'var(--color-text-secondary)',
                                    display: 'flex',
                                    alignItems: 'center',
                                    gap: '0.75rem'
                                }}>
                                    <span style={{ fontSize: '1.2rem', opacity: 0.8 }}>{flag.icon}</span>
                                    <span>{flag.text}</span>
                                </div>
                            ))}
                        </div>
                    </div>
                )}

                {/* Actions */}
                <div className="actions-modern" style={{ textAlign: 'center', marginTop: '4rem' }}>
                    <button
                        className="btn-modern btn-modern-primary"
                        onClick={onAnalyzeNew}
                        style={{
                            background: 'var(--color-text-primary)',
                            color: '#fff',
                            border: 'none',
                            padding: '1rem 2.5rem',
                            borderRadius: '100px',
                            fontSize: '0.95rem',
                            fontWeight: 500,
                            letterSpacing: '0.02em',
                            cursor: 'pointer',
                            transition: 'all 0.2s',
                            boxShadow: 'var(--shadow-md)'
                        }}
                    >
                        Analyze Another Product
                    </button>
                </div>

                {/* Disclaimer */}
                <div className="disclaimer-modern" style={{ textAlign: 'center', marginTop: '3rem', opacity: 0.5 }}>
                    <p style={{ fontSize: '0.75rem', color: 'var(--color-text-tertiary)' }}>AI evaluation based on ingredient text only.</p>
                </div>
            </div>
        </section>
    );
}

export default ResultsSection;
