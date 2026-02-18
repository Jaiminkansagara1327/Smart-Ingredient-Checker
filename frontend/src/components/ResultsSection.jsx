import React, { useState, useEffect } from 'react';
import api from '../api';
import { getPrefetchedAlternatives } from './UploadSection';

// --- Ingredient Highlighting ---
// Red-flag ingredients to highlight in red
const RED_FLAG_KEYWORDS = [
    'palm oil', 'partially hydrogenated', 'hydrogenated', 'high fructose corn syrup',
    'msg', 'monosodium glutamate', 'sodium benzoate', 'potassium sorbate',
    'aspartame', 'sucralose', 'acesulfame', 'saccharin',
    'artificial', 'synthetic', 'tbhq', 'bha', 'bht',
    'sodium nitrite', 'sodium nitrate', 'propyl gallate',
    'carrageenan', 'polysorbate', 'titanium dioxide',
    'tartrazine', 'sunset yellow', 'brilliant blue', 'allura red',
    'caramel color', 'caramel colour',
];

// E-number pattern (E100-E1521)
const E_NUMBER_REGEX = /\b(e|ins)\s*\d{3,4}[a-z]?\b/gi;

// Green-flag ingredients
const GREEN_FLAG_KEYWORDS = [
    'whole wheat', 'whole grain', 'oats', 'fiber', 'fibre',
    'olive oil', 'flaxseed', 'chia', 'quinoa',
    'turmeric', 'ginger', 'garlic', 'cinnamon',
    'vitamin', 'mineral', 'iron', 'calcium', 'zinc',
    'probiotic', 'prebiotic', 'antioxidant',
    'organic', 'natural flavor', 'natural flavour',
    'honey', 'jaggery', 'coconut oil', 'millets',
];

function highlightIngredients(text) {
    if (!text) return null;

    // Split by commas but keep them
    const parts = text.split(/(,\s*)/);

    return parts.map((part, idx) => {
        const lower = part.toLowerCase().trim();

        // Check for E-numbers
        if (E_NUMBER_REGEX.test(lower)) {
            E_NUMBER_REGEX.lastIndex = 0; // Reset regex
            return <span key={idx} className="ingredient-red" title="Additive (E-number)">{part}</span>;
        }

        // Check red flags
        for (const keyword of RED_FLAG_KEYWORDS) {
            if (lower.includes(keyword)) {
                return <span key={idx} className="ingredient-red" title="Potentially concerning ingredient">{part}</span>;
            }
        }

        // Check green flags
        for (const keyword of GREEN_FLAG_KEYWORDS) {
            if (lower.includes(keyword)) {
                return <span key={idx} className="ingredient-green" title="Generally positive ingredient">{part}</span>;
            }
        }

        return <span key={idx}>{part}</span>;
    });
}

// --- Helper Functions ---
function renderOverviewValue(val) {
    if (!val) return 'Unknown';
    const s = String(val).trim();
    if (s.toLowerCase() === 'not applicable' || s.toLowerCase() === 'unknown') {
        return <span style={{ color: 'var(--color-text-tertiary)', fontSize: '0.9em' }}>Unknown</span>;
    }
    return s;
}

// --- Nutri-Score Badge ---
function NutriscoreBadge({ grade, size = 'normal' }) {
    if (!grade) return null;

    const sizeClass = size === 'small' ? 'nutriscore-badge-sm' : 'nutriscore-badge';

    // Normalize grade
    let g = grade.toLowerCase().trim();

    // Handle "unknown", "not-applicable", etc.
    if (g === 'unknown' || g === 'not-applicable' || g.length > 1) {
        return (
            <span className={`${sizeClass} nutriscore-unknown`}>
                NO SCORE
            </span>
        );
    }

    const colors = {
        a: '#038141',
        b: '#85BB2F',
        c: '#FECB02',
        d: '#EE8100',
        e: '#E63E11',
    };
    const bg = colors[g] || '#888';

    return (
        <span className={sizeClass} style={{ background: bg }}>
            {g.toUpperCase()}
        </span>
    );
}

// --- Serving Size Definitions ---
const SERVING_OPTIONS = [
    { label: '100g', grams: 100 },
    { label: '50g', grams: 50 },
    { label: '1 Bowl', grams: 200 },
    { label: '1 Serving', grams: 30 },
];

// --- Nutrient Definitions ---
const NUTRIENT_DEFS = [
    { key: 'energy_kcal', label: 'Calories', unit: 'kcal' },
    { key: 'proteins', label: 'Protein', unit: 'g' },
    { key: 'fat', label: 'Total Fat', unit: 'g' },
    { key: 'saturated_fat', label: 'Saturated Fat', unit: 'g' },
    { key: 'carbohydrates', label: 'Carbs', unit: 'g' },
    { key: 'sugars', label: 'Sugar', unit: 'g' },
    { key: 'fiber', label: 'Fiber', unit: 'g' },
    { key: 'salt', label: 'Salt', unit: 'g' },
];

// --- Nutrition Panel ---
function NutritionPanel({ nutriments }) {
    const [selectedServing, setSelectedServing] = useState(0);
    const [customGrams, setCustomGrams] = useState('');
    const [isCustom, setIsCustom] = useState(false);

    if (!nutriments) {
        return (
            <div className="results-card nutrition-panel">
                <h3 className="results-section-title">Nutrition Facts</h3>
                <p className="nutrition-unavailable">
                    Nutrition data is not available for this product.
                </p>
            </div>
        );
    }

    const grams = isCustom
        ? (parseFloat(customGrams) || 0)
        : SERVING_OPTIONS[selectedServing].grams;
    const multiplier = grams / 100;

    return (
        <div className="results-card nutrition-panel">
            <h3 className="results-section-title">Nutrition Facts</h3>

            {/* Serving Size Selector */}
            <div className="serving-selector">
                {SERVING_OPTIONS.map((option, idx) => (
                    <button
                        key={option.label}
                        className={`serving-btn ${!isCustom && idx === selectedServing ? 'active' : ''}`}
                        onClick={() => { setSelectedServing(idx); setIsCustom(false); }}
                    >
                        {option.label}
                    </button>
                ))}
                <div className={`serving-btn serving-btn-custom ${isCustom ? 'active' : ''}`} onClick={() => setIsCustom(true)}>
                    <input
                        type="number"
                        className="serving-custom-input"
                        placeholder="Custom"
                        min="1"
                        max="5000"
                        value={customGrams}
                        onFocus={() => setIsCustom(true)}
                        onChange={(e) => {
                            setCustomGrams(e.target.value);
                            setIsCustom(true);
                        }}
                        onClick={(e) => e.stopPropagation()}
                    />
                    <span className="serving-custom-unit">g</span>
                </div>
            </div>

            {/* Nutrient Grid */}
            <div className="nutrition-grid">
                {NUTRIENT_DEFS.map((nutrient) => {
                    const rawVal = nutriments[nutrient.key];
                    const value = rawVal != null
                        ? (rawVal * multiplier).toFixed(nutrient.key === 'energy_kcal' ? 0 : 1)
                        : '–';
                    return (
                        <div key={nutrient.key} className="nutrient-card">
                            <span className="nutrient-value">
                                {value}
                                {rawVal != null && <span className="nutrient-unit"> {nutrient.unit}</span>}
                            </span>
                            <span className="nutrient-label">{nutrient.label}</span>
                        </div>
                    );
                })}
            </div>

            <p className="nutrition-disclaimer">Values may vary from product packaging.</p>
        </div>
    );
}

// --- Scan History (localStorage) ---
const HISTORY_KEY = 'ingrexa_scan_history';
const MAX_HISTORY = 10;

function getScanHistory() {
    try {
        return JSON.parse(localStorage.getItem(HISTORY_KEY) || '[]');
    } catch {
        return [];
    }
}

function addToScanHistory(product) {
    if (!product || !product.name) return;
    const history = getScanHistory();
    // Remove duplicate
    const filtered = history.filter(h => h.name !== product.name);
    // Add to front
    filtered.unshift({
        name: product.name,
        brand: product.brand || '',
        image_url: product.image_url || '',
        barcode: product.barcode || '',
        nutriscore_grade: product.nutriscore_grade || '',
        scannedAt: new Date().toISOString(),
    });
    // Limit
    localStorage.setItem(HISTORY_KEY, JSON.stringify(filtered.slice(0, MAX_HISTORY)));
}


function ResultsSection({ data, image, onAnalyzeNew }) {
    const [alternatives, setAlternatives] = useState([]);
    const [loadingAlternatives, setLoadingAlternatives] = useState(false);
    const [showRawIngredients, setShowRawIngredients] = useState(false);

    if (!data) return null;

    const hasNewFormat = data.overview && data.frequency_verdict && data.ingredient_breakdown;
    const meta = data._product_meta || {};
    const rawIngredientsText = data.raw_ingredients_text || meta.ingredients_text || '';

    // Save to scan history on mount
    useEffect(() => {
        if (meta.name) {
            addToScanHistory(meta);
        }
    }, [meta.name]);

    // Fetch healthier alternatives (use prefetched if available)
    useEffect(() => {
        if (!meta.categories) return;

        // ⚡ Check prefetch cache first — instant load
        const prefetched = getPrefetchedAlternatives(
            meta.categories, meta.nutriscore_grade || '', meta.name || ''
        );
        if (prefetched) {
            setAlternatives(prefetched);
            return; // No need to fetch!
        }

        setLoadingAlternatives(true);
        api.get('/api/alternatives/', {
            params: {
                category: meta.categories,
                nutriscore: meta.nutriscore_grade || '',
                name: meta.name || '',
            },
            timeout: 12000,
        })
            .then(res => {
                if (res.data.success && res.data.alternatives) {
                    setAlternatives(res.data.alternatives);
                }
            })
            .catch(err => console.error('Alternatives fetch error:', err))
            .finally(() => setLoadingAlternatives(false));
    }, [meta.categories, meta.nutriscore_grade, meta.name]);

    if (!hasNewFormat) {
        return <div style={{ textAlign: 'center', padding: '3rem' }}>
            <p>Analysis format not recognized. Please re-analyze.</p>
        </div>;
    }

    return (
        <section className="results-section">
            <div className="results-container" style={{ maxWidth: '900px', margin: '0 auto', padding: 'var(--spacing-2xl)' }}>

                {/* SECTION 1: Product Overview */}
                <div className="results-card">
                    <h3 className="results-section-title">Product Overview</h3>

                    {/* Product identity row */}
                    {meta.name && (
                        <div className="product-identity-row">
                            {meta.image_url && (
                                <img src={meta.image_url} alt={meta.name} className="product-identity-img" />
                            )}
                            <div className="product-identity-info">
                                <span className="product-identity-name">{meta.name}</span>
                                {meta.brand && <span className="product-identity-brand">{meta.brand}</span>}
                            </div>
                            {meta.nutriscore_grade && <NutriscoreBadge grade={meta.nutriscore_grade} />}
                        </div>
                    )}

                    <div style={{
                        display: 'grid',
                        gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))',
                        gap: 'var(--spacing-lg)'
                    }}>
                        <div className="overview-stat-card">
                            <p className="overview-stat-label">Processing Level</p>
                            <p className="overview-stat-value">{renderOverviewValue(data.overview.processing_level)}</p>
                        </div>
                        <div className="overview-stat-card">
                            <p className="overview-stat-label">Ingredients</p>
                            <p className="overview-stat-value">{renderOverviewValue(data.overview.ingredient_count)}</p>
                        </div>
                        <div className="overview-stat-card">
                            <p className="overview-stat-label">Additives</p>
                            <p className="overview-stat-value">{renderOverviewValue(data.overview.additives_present)}</p>
                        </div>
                    </div>
                </div>

                {/* SECTION 2: Frequency Verdict */}
                <div className="verdict-card">
                    <h3 className="results-section-title" style={{ color: 'var(--color-accent-secondary)' }}>
                        Frequency Verdict
                    </h3>
                    <p className="verdict-text">{data.frequency_verdict}</p>
                </div>

                {/* SECTION 3: Key Signals */}
                <div className="results-card">
                    <h3 className="results-section-title">Key Signals</h3>
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
                            <div key={idx} className="overview-stat-card" style={{ border: '1px solid var(--color-border)' }}>
                                <p className="overview-stat-label">{signal.label}</p>
                                <p className="overview-stat-value">{signal.value}</p>
                            </div>
                        ))}
                    </div>
                </div>

                {/* SECTION 3.5: Nutrition Facts */}
                <NutritionPanel nutriments={meta.nutriments} />

                {/* SECTION 4: Ingredient Breakdown (with color highlighting) */}
                <div className="results-card">
                    <h3 className="results-section-title">Ingredient Breakdown</h3>

                    {/* Color legend */}
                    <div className="ingredient-legend">
                        <span className="legend-item"><span className="legend-dot red"></span> Concerning</span>
                        <span className="legend-item"><span className="legend-dot green"></span> Positive</span>
                        <span className="legend-item"><span className="legend-dot neutral"></span> Neutral</span>
                    </div>

                    <div>
                        {data.ingredient_breakdown.map((item, idx) => (
                            <div key={idx} className="ingredient-row">
                                <span className={`ingredient-name ${item.risk === '🔴' || item.risk === '🟡' ? 'flagged-red' :
                                    item.risk === '🟢' ? 'flagged-green' : ''
                                    }`}>
                                    {item.name}
                                </span>
                                <span className="ingredient-role">{item.role}</span>
                                <span className="ingredient-risk">{item.risk}</span>
                            </div>
                        ))}
                    </div>
                </div>

                {/* SECTION 4.5: Raw Ingredient Highlight */}
                {rawIngredientsText && (
                    <div className="results-card">
                        <button
                            className="raw-ingredients-toggle"
                            onClick={() => setShowRawIngredients(!showRawIngredients)}
                        >
                            <span>{showRawIngredients ? '▾' : '▸'} View Raw Ingredient List</span>
                        </button>
                        {showRawIngredients && (
                            <div className="raw-ingredients-text">
                                {highlightIngredients(rawIngredientsText)}
                            </div>
                        )}
                    </div>
                )}

                {/* SECTION 5: Who Should Limit */}
                {data.limit_groups && data.limit_groups.length > 0 && (
                    <div className="results-card warning-card">
                        <h3 className="results-section-title" style={{ color: 'var(--color-warning)' }}>
                            Who Should Limit This
                        </h3>
                        <ul style={{ listStyle: 'none', padding: 0, margin: 0 }}>
                            {data.limit_groups.map((group, idx) => (
                                <li key={idx} className="limit-group-item">
                                    <span className="limit-dot">•</span>
                                    {group}
                                </li>
                            ))}
                        </ul>
                    </div>
                )}

                {/* SECTION 6: Healthier Alternatives */}
                {(loadingAlternatives || alternatives.length > 0) && (
                    <div className="results-card alternatives-card">
                        <h3 className="results-section-title" style={{ color: 'var(--color-success)' }}>
                            🔄 Healthier Alternatives
                        </h3>

                        {loadingAlternatives ? (
                            <div className="alternatives-loading">
                                <div className="alt-skeleton"></div>
                                <div className="alt-skeleton"></div>
                                <div className="alt-skeleton"></div>
                            </div>
                        ) : (
                            <div className="alternatives-grid">
                                {alternatives.map((alt, idx) => (
                                    <div key={alt.barcode || idx} className="alternative-item">
                                        <div className="alt-image-wrapper">
                                            {alt.image_url ? (
                                                <img
                                                    src={alt.image_url}
                                                    alt={alt.name}
                                                    className="alt-product-img"
                                                    loading="lazy"
                                                    onError={(e) => { e.target.style.display = 'none'; }}
                                                />
                                            ) : (
                                                <div className="alt-image-placeholder">📦</div>
                                            )}
                                        </div>
                                        <div className="alt-info">
                                            <span className="alt-name">{alt.name}</span>
                                            <span className="alt-brand">{alt.brand}</span>
                                        </div>
                                        <NutriscoreBadge grade={alt.nutriscore_grade} size="small" />
                                    </div>
                                ))}
                            </div>
                        )}
                    </div>
                )}

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
                <div style={{
                    marginTop: 'var(--spacing-2xl)',
                    display: 'flex',
                    justifyContent: 'center'
                }}>
                    <button
                        className="analyze-btn"
                        onClick={onAnalyzeNew}
                        style={{
                            width: '100%',
                            maxWidth: '500px',
                            fontSize: 'var(--font-size-lg)',
                            padding: 'var(--spacing-lg)',
                            boxShadow: 'var(--shadow-xl)'
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
