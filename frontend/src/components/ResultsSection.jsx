import React from 'react';

function ResultsSection({ data, image, onAnalyzeNew }) {
    if (!data) return null;

    // Check if we have the new structured format
    const hasNewFormat = data.overview && data.frequency_verdict && data.ingredient_breakdown;

    if (!hasNewFormat) {
        // Fallback for old format
        return <div style={{ textAlign: 'center', padding: '3rem' }}>
            <p>Analysis format not recognized. Please re-analyze.</p>
        </div>;
    }

    return (
        <section className="results-section">
            <div className="results-container" style={{ maxWidth: '900px', margin: '0 auto', padding: 'var(--spacing-2xl)' }}>

                {/* SECTION 1: Product Overview */}
                <div style={{
                    background: 'var(--color-bg-card)',
                    padding: 'var(--spacing-xl)',
                    borderRadius: 'var(--radius-xl)',
                    border: '1px solid var(--color-border)',
                    boxShadow: 'var(--shadow-md)',
                    marginBottom: 'var(--spacing-xl)',
                    textAlign: 'center'
                }}>
                    <h3 style={{
                        fontSize: 'var(--font-size-xs)',
                        textTransform: 'uppercase',
                        letterSpacing: '0.15em',
                        color: 'var(--color-text-tertiary)',
                        marginBottom: 'var(--spacing-lg)',
                        fontWeight: 600
                    }}>
                        Product Overview
                    </h3>
                    <div style={{
                        display: 'grid',
                        gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))',
                        gap: 'var(--spacing-lg)'
                    }}>
                        <div style={{ padding: 'var(--spacing-md)', background: 'var(--color-bg-secondary)', borderRadius: 'var(--radius-md)' }}>
                            <p style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-tertiary)', marginBottom: 'var(--spacing-xs)', fontWeight: 500 }}>Processing Level</p>
                            <p style={{ fontSize: 'var(--font-size-base)', fontWeight: 600, color: 'var(--color-text-primary)' }}>{data.overview.processing_level}</p>
                        </div>
                        <div style={{ padding: 'var(--spacing-md)', background: 'var(--color-bg-secondary)', borderRadius: 'var(--radius-md)' }}>
                            <p style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-tertiary)', marginBottom: 'var(--spacing-xs)', fontWeight: 500 }}>Ingredients</p>
                            <p style={{ fontSize: 'var(--font-size-base)', fontWeight: 600, color: 'var(--color-text-primary)' }}>{data.overview.ingredient_count}</p>
                        </div>
                        <div style={{ padding: 'var(--spacing-md)', background: 'var(--color-bg-secondary)', borderRadius: 'var(--radius-md)' }}>
                            <p style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-tertiary)', marginBottom: 'var(--spacing-xs)', fontWeight: 500 }}>Additives</p>
                            <p style={{ fontSize: 'var(--font-size-base)', fontWeight: 600, color: 'var(--color-text-primary)' }}>{data.overview.additives_present}</p>
                        </div>
                    </div>
                </div>

                {/* SECTION 2: Frequency Verdict (Prominent) */}
                <div style={{
                    textAlign: 'center',
                    marginBottom: 'var(--spacing-xl)',
                    padding: 'var(--spacing-2xl)',
                    background: 'var(--color-accent-light)',
                    borderRadius: 'var(--radius-xl)',
                    border: '2px solid var(--color-accent-primary)',
                    boxShadow: 'var(--shadow-lg)'
                }}>
                    <h3 style={{
                        fontSize: 'var(--font-size-xs)',
                        textTransform: 'uppercase',
                        letterSpacing: '0.15em',
                        color: 'var(--color-accent-secondary)',
                        marginBottom: 'var(--spacing-md)',
                        fontWeight: 600
                    }}>
                        Frequency Verdict
                    </h3>
                    <p style={{
                        fontSize: 'var(--font-size-2xl)',
                        fontWeight: 600,
                        color: 'var(--color-text-primary)',
                        lineHeight: '1.4'
                    }}>
                        {data.frequency_verdict}
                    </p>
                </div>

                {/* SECTION 3: Key Signals */}
                <div style={{
                    background: 'var(--color-bg-card)',
                    padding: 'var(--spacing-xl)',
                    borderRadius: 'var(--radius-xl)',
                    border: '1px solid var(--color-border)',
                    boxShadow: 'var(--shadow-md)',
                    marginBottom: 'var(--spacing-xl)'
                }}>
                    <h3 style={{
                        fontSize: 'var(--font-size-xs)',
                        textTransform: 'uppercase',
                        letterSpacing: '0.15em',
                        color: 'var(--color-text-tertiary)',
                        marginBottom: 'var(--spacing-lg)',
                        fontWeight: 600,
                        textAlign: 'center'
                    }}>
                        Key Signals
                    </h3>
                    <div style={{
                        display: 'grid',
                        gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))',
                        gap: 'var(--spacing-md)'
                    }}>
                        {[
                            { label: 'Added Sugar', value: data.key_signals.added_sugar },
                            { label: 'Refined Flour', value: data.key_signals.refined_flour_starch },
                            { label: 'Artificial Colors', value: data.key_signals.artificial_colors },
                            { label: 'Preservatives', value: data.key_signals.preservatives },
                            { label: 'Artificial Flavors', value: data.key_signals.artificial_flavors }
                        ].map((signal, idx) => (
                            <div key={idx} style={{
                                padding: 'var(--spacing-md)',
                                background: 'var(--color-bg-secondary)',
                                borderRadius: 'var(--radius-md)',
                                textAlign: 'center',
                                border: '1px solid var(--color-border)'
                            }}>
                                <p style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-tertiary)', marginBottom: 'var(--spacing-xs)' }}>{signal.label}</p>
                                <p style={{ fontSize: 'var(--font-size-base)', fontWeight: 600, color: 'var(--color-text-primary)' }}>{signal.value}</p>
                            </div>
                        ))}
                    </div>
                </div>

                {/* SECTION 4: Ingredient Breakdown */}
                <div style={{
                    background: 'var(--color-bg-card)',
                    padding: 'var(--spacing-xl)',
                    borderRadius: 'var(--radius-xl)',
                    border: '1px solid var(--color-border)',
                    boxShadow: 'var(--shadow-md)',
                    marginBottom: 'var(--spacing-xl)'
                }}>
                    <h3 style={{
                        fontSize: 'var(--font-size-xs)',
                        textTransform: 'uppercase',
                        letterSpacing: '0.15em',
                        color: 'var(--color-text-tertiary)',
                        marginBottom: 'var(--spacing-lg)',
                        fontWeight: 600,
                        textAlign: 'center'
                    }}>
                        Ingredient Breakdown
                    </h3>
                    <div>
                        {data.ingredient_breakdown.map((item, idx) => (
                            <div key={idx} style={{
                                display: 'flex',
                                justifyContent: 'space-between',
                                alignItems: 'center',
                                padding: 'var(--spacing-md)',
                                borderBottom: idx < data.ingredient_breakdown.length - 1 ? '1px solid var(--color-border)' : 'none',
                                gap: 'var(--spacing-md)'
                            }}>
                                <span style={{ flex: '1', fontSize: 'var(--font-size-base)', color: 'var(--color-text-primary)' }}>{item.name}</span>
                                <span style={{
                                    fontSize: 'var(--font-size-xs)',
                                    color: 'var(--color-text-secondary)',
                                    minWidth: '90px',
                                    textAlign: 'center',
                                    padding: 'var(--spacing-xs) var(--spacing-sm)',
                                    background: 'var(--color-bg-secondary)',
                                    borderRadius: 'var(--radius-sm)',
                                    fontWeight: 500
                                }}>{item.role}</span>
                                <span style={{ fontSize: '1.2rem', minWidth: '30px', textAlign: 'center' }}>{item.risk}</span>
                            </div>
                        ))}
                    </div>
                </div>

                {/* SECTION 5: Who Should Limit This */}
                {data.limit_groups && data.limit_groups.length > 0 && (
                    <div style={{
                        background: 'var(--color-warning-bg)',
                        padding: 'var(--spacing-xl)',
                        borderRadius: 'var(--radius-xl)',
                        border: '1px solid var(--color-warning-border)',
                        boxShadow: 'var(--shadow-md)',
                        marginBottom: 'var(--spacing-xl)'
                    }}>
                        <h3 style={{
                            fontSize: 'var(--font-size-xs)',
                            textTransform: 'uppercase',
                            letterSpacing: '0.15em',
                            color: 'var(--color-warning)',
                            marginBottom: 'var(--spacing-lg)',
                            fontWeight: 600,
                            textAlign: 'center'
                        }}>
                            Who Should Limit This
                        </h3>
                        <ul style={{ listStyle: 'none', padding: 0, margin: 0 }}>
                            {data.limit_groups.map((group, idx) => (
                                <li key={idx} style={{
                                    fontSize: 'var(--font-size-base)',
                                    color: 'var(--color-text-primary)',
                                    marginBottom: idx < data.limit_groups.length - 1 ? 'var(--spacing-sm)' : 0,
                                    paddingLeft: 'var(--spacing-lg)',
                                    position: 'relative'
                                }}>
                                    <span style={{ position: 'absolute', left: 0, color: 'var(--color-warning)', fontWeight: 700 }}>•</span>
                                    {group}
                                </li>
                            ))}
                        </ul>
                    </div>
                )}

                {/* SECTION 6: Bottom Line */}
                <div style={{
                    marginBottom: 'var(--spacing-xl)',
                    padding: 'var(--spacing-xl)',
                    background: 'var(--color-bg-tertiary)',
                    borderRadius: 'var(--radius-xl)',
                    border: '1px solid var(--color-border)',
                    textAlign: 'center'
                }}>
                    <h3 style={{
                        fontSize: 'var(--font-size-xs)',
                        textTransform: 'uppercase',
                        letterSpacing: '0.15em',
                        color: 'var(--color-text-tertiary)',
                        marginBottom: 'var(--spacing-md)',
                        fontWeight: 600
                    }}>
                        Bottom Line
                    </h3>
                    <p style={{
                        fontSize: 'var(--font-size-lg)',
                        lineHeight: '1.6',
                        color: 'var(--color-text-primary)',
                        fontWeight: 500
                    }}>
                        {data.bottom_line}
                    </p>
                </div>

                {/* SECTION 7: Transparency Note */}
                <div style={{
                    textAlign: 'center',
                    padding: 'var(--spacing-lg)',
                    borderTop: '1px solid var(--color-border)',
                    marginTop: 'var(--spacing-xl)'
                }}>
                    <p style={{
                        fontSize: 'var(--font-size-sm)',
                        color: 'var(--color-text-tertiary)',
                        fontStyle: 'italic',
                        lineHeight: '1.5'
                    }}>
                        {data.transparency_note}
                    </p>
                </div>

                {/* Action Button */}
                <div style={{ textAlign: 'center', marginTop: 'var(--spacing-2xl)' }}>
                    <button
                        className="analyze-btn"
                        onClick={onAnalyzeNew}
                        style={{
                            width: 'auto',
                            minWidth: '250px'
                        }}
                    >
                        Analyze Another Product
                    </button>
                </div>
            </div>
        </section>
    );
}

export default ResultsSection;
