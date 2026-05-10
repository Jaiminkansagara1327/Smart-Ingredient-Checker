import React, { useState, useEffect } from 'react';
import api from '../../api';
import { getPrefetchedAlternatives } from './UploadSection';

const RED_FLAGS = [
    'palm oil', 'partially hydrogenated', 'hydrogenated', 'high fructose corn syrup',
    'msg', 'monosodium glutamate', 'sodium benzoate', 'potassium sorbate',
    'aspartame', 'sucralose', 'acesulfame', 'saccharin',
    'artificial', 'synthetic', 'tbhq', 'bha', 'bht',
    'sodium nitrite', 'sodium nitrate', 'propyl gallate',
    'carrageenan', 'polysorbate', 'titanium dioxide',
    'tartrazine', 'sunset yellow', 'brilliant blue', 'allura red',
    'caramel color', 'caramel colour',
];

const GREEN_FLAGS = [
    'whole wheat', 'whole grain', 'oats', 'fiber', 'fibre',
    'olive oil', 'flaxseed', 'chia', 'quinoa',
    'turmeric', 'ginger', 'garlic', 'cinnamon',
    'vitamin', 'mineral', 'iron', 'calcium', 'zinc',
    'probiotic', 'prebiotic', 'antioxidant',
    'organic', 'natural flavor', 'natural flavour',
    'honey', 'jaggery', 'coconut oil', 'millets',
];

const E_NUMBER = /\b(e|ins)\s*\d{3,4}[a-z]?\b/gi;

function highlightIngredients(text) {
    if (!text) return null;
    return text.split(/(,\s*)/).map((part, idx) => {
        const lower = part.toLowerCase().trim();
        if (E_NUMBER.test(lower)) { E_NUMBER.lastIndex = 0; return <span key={idx} className="ingredient-red" title="Additive">{part}</span>; }
        if (RED_FLAGS.some(k => lower.includes(k))) return <span key={idx} className="ingredient-red">{part}</span>;
        if (GREEN_FLAGS.some(k => lower.includes(k))) return <span key={idx} className="ingredient-green">{part}</span>;
        return <span key={idx}>{part}</span>;
    });
}

function stripEmojis(text) {
    if (!text) return '';
    return text.replace(/[\u{1F300}-\u{1F9FF}]|[\u{2600}-\u{26FF}]/gu, '').trim();
}

function renderValue(val) {
    if (!val) return 'Unknown';
    const s = String(val).trim();
    if (['not applicable', 'unknown'].includes(s.toLowerCase())) {
        return <span style={{ color: 'var(--color-text-tertiary)', fontSize: '0.9em' }}>Unknown</span>;
    }
    return s;
}

function ScoreBadge({ score, grade, size = 'normal' }) {
    if (score === undefined && !grade) return null;
    const cls = size === 'small' ? 'nutriscore-badge-sm' : 'nutriscore-badge';

    let val = 0;
    let estimated = false;

    if (score !== undefined) {
        val = Number(score);
        if (val > 10) val = val / 10;
    } else if (grade) {
        const g = grade.toLowerCase().trim();
        if (g === 'unknown' || g === 'not-applicable' || g.length > 1) {
            return <span className={`${cls} nutriscore-unknown`}>NO SCORE</span>;
        }
        val = { a: 9.0, b: 7.0, c: 5.0, d: 3.0, e: 1.0 }[g] || 0;
        estimated = true;
    }

    let bg = '#E63E11';
    if (val >= 8) bg = '#038141';
    else if (val >= 6) bg = '#85BB2F';
    else if (val >= 4) bg = '#FECB02';
    else if (val >= 2) bg = '#EE8100';

    return (
        <span className={cls} style={{ background: bg, color: '#fff', padding: '4px 10px', borderRadius: '6px', fontWeight: 'bold' }} title={estimated ? 'Estimated from Nutri-Score' : 'Calculated score'}>
            {val.toFixed(1)} / 10
        </span>
    );
}

function parseServingGrams(str) {
    if (!str) return null;
    const match = str.match(/(\d+\.?\d*)\s*(g|gm|ml|cl|l)\b/i);
    if (!match) return null;
    const val = parseFloat(match[1]);
    const unit = match[2].toLowerCase();
    if (unit === 'cl') return val * 10;
    if (unit === 'l') return val * 1000;
    return val;
}

function NutritionPanel({ nutriments }) {
    const [selectedServing, setSelectedServing] = useState(0);
    const [customGrams, setCustomGrams] = useState('');
    const [isCustom, setIsCustom] = useState(false);

    if (!nutriments?.rows?.length) {
        return (
            <div className="results-card nutrition-panel">
                <h3 className="results-section-title">Nutrition Facts</h3>
                <div className="nutrition-unavailable">
                    <p className="nutrition-unavailable-title">Nutrition data unavailable</p>
                    <p className="nutrition-unavailable-desc">Please refer to the product packaging for nutritional values.</p>
                </div>
            </div>
        );
    }

    const { rows, serving_size: servingSize = '', is_liquid: isLiquid = false } = nutriments;
    const baseUnit = isLiquid ? 'ml' : 'g';
    const actualServing = parseServingGrams(servingSize);

    const options = [];
    if (actualServing && actualServing !== 100) options.push({ label: `1 Serving (${actualServing}${baseUnit})`, grams: actualServing });
    if (isLiquid) {
        options.push({ label: '1 Glass (250ml)', grams: 250 });
        options.push({ label: '1 Can (330ml)', grams: 330 });
    } else {
        options.push({ label: '50g', grams: 50 });
        options.push({ label: '1 Bowl (200g)', grams: 200 });
    }

    const amount = isCustom ? (parseFloat(customGrams) || 0) : options[selectedServing]?.grams || 100;
    const multiplier = amount / 100;
    const isBase = !isCustom && amount === 100;
    const servingLabel = isCustom ? (customGrams ? `Per ${customGrams}${baseUnit}` : 'Per —') : `Per ${options[selectedServing]?.label || '100' + baseUnit}`;

    const fmt = (val, unit) => {
        if (unit === 'kcal' || unit === 'kJ') return Math.round(val);
        if (val < 0.1 && val > 0) return '<0.1';
        return val.toFixed(1);
    };

    return (
        <div className="results-card nutrition-panel">
            <h3 className="results-section-title">Nutrition Facts</h3>
            {servingSize && <p className="nutrition-serving-size">Serving size: {servingSize}</p>}

            <div className="serving-selector">
                {options.map((opt, idx) => (
                    <button key={opt.label} className={`serving-btn ${!isCustom && idx === selectedServing ? 'active' : ''}`} onClick={() => { setSelectedServing(idx); setIsCustom(false); }}>
                        {opt.label}
                    </button>
                ))}
                <div className={`serving-btn serving-btn-custom ${isCustom ? 'active' : ''}`} onClick={() => setIsCustom(true)}>
                    <input
                        type="number"
                        className="serving-custom-input"
                        placeholder="Custom"
                        min="1" max="5000"
                        value={customGrams}
                        onFocus={() => setIsCustom(true)}
                        onChange={(e) => { setCustomGrams(e.target.value); setIsCustom(true); }}
                        onClick={(e) => e.stopPropagation()}
                    />
                    <span className="serving-custom-unit">{baseUnit}</span>
                </div>
            </div>

            <div className="nutrition-table-wrapper">
                <table className="nutrition-table">
                    <thead>
                        <tr>
                            <th className="nt-label-col">Nutrient</th>
                            <th className="nt-val-col">Per 100{baseUnit}</th>
                            {!isBase && <th className="nt-val-col nt-serving-col">{servingLabel}</th>}
                        </tr>
                    </thead>
                    <tbody>
                        {rows.map((row, idx) => (
                            <tr key={idx}>
                                <td className="nt-label">{row.label}</td>
                                <td className="nt-value">{fmt(row.value, row.unit)} {row.unit}</td>
                                {!isBase && (
                                    <td className="nt-value nt-serving-val">
                                        {amount > 0 ? `${fmt(row.value * multiplier, row.unit)} ${row.unit}` : '—'}
                                    </td>
                                )}
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
            <p className="nutrition-disclaimer">Values may vary from product packaging.</p>
        </div>
    );
}

const HISTORY_KEY = 'ingrexa_scan_history';

function addToHistory(product) {
    if (!product?.name) return;
    try {
        const history = JSON.parse(localStorage.getItem(HISTORY_KEY) || '[]');
        const filtered = history.filter(h => h.name !== product.name);
        filtered.unshift({
            name: product.name,
            brand: product.brand || '',
            image_url: product.image_url || '',
            barcode: product.barcode || '',
            nutriscore_grade: product.nutriscore_grade || '',
            scannedAt: new Date().toISOString(),
        });
        localStorage.setItem(HISTORY_KEY, JSON.stringify(filtered.slice(0, 1000)));
    } catch {}
}

function ResultsSection({ data, image, onAnalyzeNew, onNavigate }) {
    const [expandedIdx, setExpandedIdx] = useState(null);

    if (!data) return null;

    const hasFormat = data.overview && data.frequency_verdict && data.ingredient_breakdown;
    const meta = data._product_meta || {};

    useEffect(() => {
        if (meta.name) addToHistory(meta);
    }, [meta.name]);

    if (!hasFormat) {
        return <div style={{ textAlign: 'center', padding: '3rem' }}><p>Analysis format not recognized. Please re-analyze.</p></div>;
    }

    return (
        <section className="results-section">
            <div className="results-container" style={{ maxWidth: '900px', margin: '0 auto', padding: 'var(--spacing-2xl)' }}>

                {/* Product Overview */}
                <div className="results-card product-card">
                    {meta.name ? (
                        <div className="product-header">
                            <div className="product-header-top">
                                {meta.image_url && (
                                    <div className="product-img-box">
                                        <img src={meta.image_url} alt={meta.name} className="product-header-img" />
                                    </div>
                                )}
                                <div className="product-header-info">
                                    <span className="product-header-brand">{meta.brand || 'Unknown Brand'}</span>
                                    <h2 className="product-header-name">{meta.name}</h2>
                                    {data.details?.goal_used && (
                                        <div className="product-config-badges">
                                            <span className="config-badge">🎯 {data.details.goal_used}</span>
                                            <span className="config-badge">🥣 {data.details.type_used}</span>
                                        </div>
                                    )}
                                </div>
                                <div className="score-wrapper">
                                    <ScoreBadge score={data.score} grade={meta.nutriscore_grade} />
                                    <div className="score-math-link" onClick={() => onNavigate('scoring')}>Methodology</div>
                                </div>
                            </div>
                        </div>
                    ) : (
                        <div className="manual-ingredients-notice">
                            <p>Analyzed from manually entered ingredients</p>
                            {data.details?.goal_used && (
                                <div className="product-config-badges">
                                    <span className="config-badge">🎯 {data.details.goal_used}</span>
                                    <span className="config-badge">🥣 {data.details.type_used}</span>
                                </div>
                            )}
                        </div>
                    )}

                    <div className="overview-stats-grid" style={{ marginTop: '1.5rem', paddingTop: '1.5rem', borderTop: '1px solid var(--color-border)' }}>
                        <div className="overview-stat-card">
                            <p className="overview-stat-label">Processing</p>
                            <p className="overview-stat-value">{renderValue(data.overview.processing_level)}</p>
                        </div>
                        <div className="overview-stat-card">
                            <p className="overview-stat-label">Ingredients</p>
                            <p className="overview-stat-value">{renderValue(data.overview.ingredient_count)}</p>
                        </div>
                        <div className="overview-stat-card">
                            <p className="overview-stat-label">Additives</p>
                            <p className="overview-stat-value">{renderValue(data.overview.additives_present)}</p>
                        </div>
                    </div>
                </div>

                {/* Verdict */}
                <div className="verdict-card">
                    <h3 className="results-section-title">Verdict</h3>
                    <p className="verdict-text">{stripEmojis(data.frequency_verdict)}</p>
                </div>

                {/* Key Signals */}
                <div className="results-card">
                    <h3 className="results-section-title">Key Signals</h3>
                    <div className="signals-grid">
                        {[
                            { label: 'Added Sugar', value: data.key_signals.added_sugar },
                            { label: 'Refined Flour', value: data.key_signals.refined_flour_starch },
                            { label: 'Artificial Colors', value: data.key_signals.artificial_colors },
                            { label: 'Preservatives', value: data.key_signals.preservatives },
                            { label: 'Artificial Flavors', value: data.key_signals.artificial_flavors },
                        ].map((s, idx) => (
                            <div key={idx} className="overview-stat-card">
                                <p className="overview-stat-label">{s.label}</p>
                                <p className="overview-stat-value">{renderValue(s.value)}</p>
                            </div>
                        ))}
                    </div>
                </div>

                {/* Nutrition */}
                <NutritionPanel nutriments={meta.nutriments} />

                {/* Ingredients */}
                <div className="results-card">
                    <h3 className="results-section-title">Ingredient Intelligence</h3>
                    <p className="breakdown-hint">Click an ingredient to understand its role.</p>

                    <div className="ingredient-legend-premium">
                        <span className="legend-item"><span className="legend-dot red"></span> Concern</span>
                        <span className="legend-item"><span className="legend-dot green"></span> Healthful</span>
                        <span className="legend-item"><span className="legend-dot neutral"></span> Neutral</span>
                    </div>

                    <div className="ingredient-list">
                        {data.ingredient_breakdown.map((item, idx) => (
                            <div key={idx} className="ingredient-group">
                                <div
                                    className={`ingredient-row ${expandedIdx === idx ? 'expanded' : ''}`}
                                    onClick={() => setExpandedIdx(expandedIdx === idx ? null : idx)}
                                >
                                    <div className={`risk-indicator ${item.risk === '🔴' ? 'risk-high' : item.risk === '🟡' ? 'risk-mod' : 'risk-low'}`}></div>
                                    <div className="ingredient-main-info">
                                        <span className={`ingredient-name ${item.risk === '🔴' || item.risk === '🟡' ? 'flagged-red' : item.risk === '🟢' ? 'flagged-green' : ''}`}>
                                            {item.name}
                                        </span>
                                    </div>
                                    <span className="ingredient-role">{item.role}</span>
                                    <span className="expand-icon">{expandedIdx === idx ? '▲' : '▼'}</span>
                                </div>
                                {expandedIdx === idx && (
                                    <div className="ingredient-explanation">
                                        <div className="explanation-label">Intelligence:</div>
                                        {item.description || 'Common food component.'}
                                    </div>
                                )}
                            </div>
                        ))}
                    </div>
                </div>

                {data.transparency_note && (
                    <div style={{ textAlign: 'center', padding: 'var(--spacing-lg)', borderTop: '1px solid var(--color-border)', marginTop: 'var(--spacing-xl)' }}>
                        <p style={{ fontSize: 'var(--font-size-sm)', color: 'var(--color-text-tertiary)', fontStyle: 'italic', lineHeight: '1.5' }}>
                            {data.transparency_note}
                        </p>
                    </div>
                )}

                <div style={{ marginTop: 'var(--spacing-2xl)', display: 'flex', justifyContent: 'center' }}>
                    <button
                        className="analyze-btn"
                        onClick={onAnalyzeNew}
                        style={{ width: '100%', maxWidth: '500px', fontSize: 'var(--font-size-lg)', padding: 'var(--spacing-lg)', boxShadow: 'var(--shadow-xl)' }}
                    >
                        Analyze Another Product
                    </button>
                </div>
            </div>
        </section>
    );
}

export default ResultsSection;
