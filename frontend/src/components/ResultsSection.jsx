import React from 'react';

function ResultsSection({ data, image, onAnalyzeNew }) {
    if (!data) return null;

    // Check if we have the new structured format
    const hasNewFormat = data.overview && data.frequency_verdict && data.ingredient_breakdown;

    if (!hasNewFormat) {
        // Fallback for old format (shouldn't happen, but safe)
        return <div style={{ textAlign: 'center', padding: '3rem' }}>
            <p>Analysis format not recognized. Please re-analyze.</p>
        </div>;
    }

    return (
        <section className="results-section">
            <div className="results-container-new" style={{
                maxWidth: '900px',
                margin: '0 auto',
                padding: '2rem 1rem'
            }}>

                {/* SECTION 1: Product Overview */}
                <div style={{ textAlign: 'center', marginBottom: '3rem', paddingBottom: '2rem', borderBottom: '1px solid var(--color-border)' }}>
                    <h3 style={{
                        fontSize: '0.75rem',
                        textTransform: 'uppercase',
                        letterSpacing: '0.15em',
                        color: 'var(--color-text-tertiary)',
                        marginBottom: '1.5rem',
                        fontWeight: 600
                    }}>
                        Product Overview
                    </h3>
                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))', gap: '1.5rem', maxWidth: '600px', margin: '0 auto' }}>
                        <div>
                            <p style={{ fontSize: '0.7rem', color: 'var(--color-text-tertiary)', marginBottom: '0.25rem', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Processing Level</p>
                            <p style={{ fontSize: '1rem', fontWeight: 600, color: 'var(--color-text-primary)' }}>{data.overview.processing_level}</p>
                        </div>
                        <div>
                            <p style={{ fontSize: '0.7rem', color: 'var(--color-text-tertiary)', marginBottom: '0.25rem', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Ingredient Count</p>
                            <p style={{ fontSize: '1rem', fontWeight: 600, color: 'var(--color-text-primary)' }}>{data.overview.ingredient_count} ingredients</p>
                        </div>
                        <div>
                            <p style={{ fontSize: '0.7rem', color: 'var(--color-text-tertiary)', marginBottom: '0.25rem', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Additives Present</p>
                            <p style={{ fontSize: '1rem', fontWeight: 600, color: 'var(--color-text-primary)' }}>{data.overview.additives_present}</p>
                        </div>
                    </div>
                </div>

                {/* SECTION 2: Frequency Verdict (Prominent) */}
                <div style={{
                    textAlign: 'center',
                    marginBottom: '3rem',
                    padding: '2rem',
                    background: 'var(--color-bg-secondary)',
                    borderRadius: '12px',
                    border: '1px solid var(--color-border)'
                }}>
                    <h3 style={{
                        fontSize: '0.75rem',
                        textTransform: 'uppercase',
                        letterSpacing: '0.15em',
                        color: 'var(--color-text-tertiary)',
                        marginBottom: '1rem',
                        fontWeight: 600
                    }}>
                        Frequency Verdict
                    </h3>
                    <p style={{
                        fontSize: '1.5rem',
                        fontWeight: 500,
                        lineHeight: '1.4',
                        color: 'var(--color-text-primary)'
                    }}>
                        {data.frequency_verdict}
                    </p>
                </div>

                {/* SECTION 3: Key Signals */}
                <div style={{ marginBottom: '3rem' }}>
                    <h3 style={{
                        fontSize: '0.75rem',
                        textTransform: 'uppercase',
                        letterSpacing: '0.15em',
                        color: 'var(--color-text-tertiary)',
                        marginBottom: '1.5rem',
                        fontWeight: 600,
                        textAlign: 'center'
                    }}>
                        Key Signals
                    </h3>
                    <div style={{
                        display: 'grid',
                        gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
                        gap: '1rem',
                        maxWidth: '700px',
                        margin: '0 auto'
                    }}>
                        <div style={{ padding: '1rem', background: 'var(--color-bg-secondary)', borderRadius: '8px', textAlign: 'center' }}>
                            <p style={{ fontSize: '0.7rem', color: 'var(--color-text-tertiary)', marginBottom: '0.5rem' }}>Added Sugar</p>
                            <p style={{ fontSize: '1rem', fontWeight: 600, color: 'var(--color-text-primary)' }}>{data.key_signals.added_sugar}</p>
                        </div>
                        <div style={{ padding: '1rem', background: 'var(--color-bg-secondary)', borderRadius: '8px', textAlign: 'center' }}>
                            <p style={{ fontSize: '0.7rem', color: 'var(--color-text-tertiary)', marginBottom: '0.5rem' }}>Refined Flour/Starch</p>
                            <p style={{ fontSize: '1rem', fontWeight: 600, color: 'var(--color-text-primary)' }}>{data.key_signals.refined_flour_starch}</p>
                        </div>
                        <div style={{ padding: '1rem', background: 'var(--color-bg-secondary)', borderRadius: '8px', textAlign: 'center' }}>
                            <p style={{ fontSize: '0.7rem', color: 'var(--color-text-tertiary)', marginBottom: '0.5rem' }}>Artificial Colors</p>
                            <p style={{ fontSize: '1rem', fontWeight: 600, color: 'var(--color-text-primary)' }}>{data.key_signals.artificial_colors}</p>
                        </div>
                        <div style={{ padding: '1rem', background: 'var(--color-bg-secondary)', borderRadius: '8px', textAlign: 'center' }}>
                            <p style={{ fontSize: '0.7rem', color: 'var(--color-text-tertiary)', marginBottom: '0.5rem' }}>Preservatives</p>
                            <p style={{ fontSize: '1rem', fontWeight: 600, color: 'var(--color-text-primary)' }}>{data.key_signals.preservatives}</p>
                        </div>
                        <div style={{ padding: '1rem', background: 'var(--color-bg-secondary)', borderRadius: '8px', textAlign: 'center' }}>
                            <p style={{ fontSize: '0.7rem', color: 'var(--color-text-tertiary)', marginBottom: '0.5rem' }}>Artificial Flavors</p>
                            <p style={{ fontSize: '1rem', fontWeight: 600, color: 'var(--color-text-primary)' }}>{data.key_signals.artificial_flavors}</p>
                        </div>
                    </div>
                </div>

                {/* SECTION 4: Ingredient Breakdown */}
                <div style={{ marginBottom: '3rem' }}>
                    <h3 style={{
                        fontSize: '0.75rem',
                        textTransform: 'uppercase',
                        letterSpacing: '0.15em',
                        color: 'var(--color-text-tertiary)',
                        marginBottom: '1.5rem',
                        fontWeight: 600,
                        textAlign: 'center'
                    }}>
                        Ingredient Breakdown
                    </h3>
                    <div style={{ maxWidth: '700px', margin: '0 auto' }}>
                        {data.ingredient_breakdown.map((item, idx) => (
                            <div key={idx} style={{
                                display: 'flex',
                                justifyContent: 'space-between',
                                alignItems: 'center',
                                padding: '0.75rem 1rem',
                                borderBottom: idx < data.ingredient_breakdown.length - 1 ? '1px solid var(--color-border)' : 'none',
                                gap: '1rem'
                            }}>
                                <span style={{ flex: '1', fontSize: '0.9rem', color: 'var(--color-text-primary)' }}>{item.name}</span>
                                <span style={{ fontSize: '0.75rem', color: 'var(--color-text-tertiary)', minWidth: '80px', textAlign: 'center' }}>{item.role}</span>
                                <span style={{ fontSize: '1.2rem', minWidth: '30px', textAlign: 'center' }}>{item.risk}</span>
                            </div>
                        ))}
                    </div>
                </div>

                {/* SECTION 5: Who Should Limit This */}
                {data.limit_groups && data.limit_groups.length > 0 && (
                    <div style={{ marginBottom: '3rem' }}>
                        <h3 style={{
                            fontSize: '0.75rem',
                            textTransform: 'uppercase',
                            letterSpacing: '0.15em',
                            color: 'var(--color-text-tertiary)',
                            marginBottom: '1.5rem',
                            fontWeight: 600,
                            textAlign: 'center'
                        }}>
                            Who Should Limit This
                        </h3>
                        <div style={{
                            maxWidth: '500px',
                            margin: '0 auto',
                            background: 'var(--color-bg-secondary)',
                            padding: '1.5rem',
                            borderRadius: '8px'
                        }}>
                            <ul style={{ listStyle: 'none', padding: 0, margin: 0 }}>
                                {data.limit_groups.map((group, idx) => (
                                    <li key={idx} style={{
                                        fontSize: '0.95rem',
                                        color: 'var(--color-text-primary)',
                                        marginBottom: idx < data.limit_groups.length - 1 ? '0.75rem' : 0,
                                        paddingLeft: '1.5rem',
                                        position: 'relative'
                                    }}>
                                        <span style={{ position: 'absolute', left: 0, color: 'var(--color-text-tertiary)' }}>•</span>
                                        {group}
                                    </li>
                                ))}
                            </ul>
                        </div>
                    </div>
                )}

                {/* SECTION 6: Bottom Line */}
                <div style={{
                    marginBottom: '3rem',
                    padding: '2rem',
                    background: 'var(--color-bg-tertiary)',
                    borderRadius: '12px',
                    textAlign: 'center'
                }}>
                    <h3 style={{
                        fontSize: '0.75rem',
                        textTransform: 'uppercase',
                        letterSpacing: '0.15em',
                        color: 'var(--color-text-tertiary)',
                        marginBottom: '1rem',
                        fontWeight: 600
                    }}>
                        Bottom Line
                    </h3>
                    <p style={{
                        fontSize: '1.1rem',
                        lineHeight: '1.6',
                        color: 'var(--color-text-primary)',
                        fontWeight: 400
                    }}>
                        {data.bottom_line}
                    </p>
                </div>

                {/* SECTION 7: Transparency Note */}
                <div style={{
                    textAlign: 'center',
                    padding: '1.5rem',
                    borderTop: '1px solid var(--color-border)',
                    marginTop: '2rem'
                }}>
                    <p style={{
                        fontSize: '0.8rem',
                        color: 'var(--color-text-tertiary)',
                        fontStyle: 'italic',
                        lineHeight: '1.5'
                    }}>
                        {data.transparency_note}
                    </p>
                </div>

                {/* Action Button */}
                <div style={{ textAlign: 'center', marginTop: '3rem' }}>
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
            </div>
        </section>
    );
}

export default ResultsSection;
