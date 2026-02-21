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

// --- Health Score Badge (Out of 10) ---
function ScoreBadge({ score, grade, size = 'normal' }) {
    if (score === undefined && !grade) return null;

    const sizeClass = size === 'small' ? 'nutriscore-badge-sm' : 'nutriscore-badge';

    let displayScore = 0;
    let isEstimate = false;

    if (score !== undefined) {
        displayScore = Number(score);
        // Defensive check: if score is > 10, it is likely inherited from an older 0-100 
        // cached API response that hasn't cleared. Gracefully scale it back to /10.
        if (displayScore > 10) {
            displayScore = displayScore / 10;
        }
    } else if (grade) {
        const g = grade.toLowerCase().trim();
        if (g === 'unknown' || g === 'not-applicable' || g.length > 1) {
            return (
                <span className={`${sizeClass} nutriscore-unknown`}>
                    NO SCORE
                </span>
            );
        }
        const gradeMap = { a: 9.0, b: 7.0, c: 5.0, d: 3.0, e: 1.0 };
        displayScore = gradeMap[g] || 0;
        isEstimate = true;
    }

    let bg = '#E63E11'; // Red (0-3.9)
    if (displayScore >= 8) bg = '#038141'; // Dark Green (8-10)
    else if (displayScore >= 6) bg = '#85BB2F'; // Light Green (6-7.9)
    else if (displayScore >= 4) bg = '#FECB02'; // Yellow (4-5.9)
    else if (displayScore >= 2) bg = '#EE8100'; // Orange (2-3.9)

    return (
        <span className={sizeClass} style={{ background: bg, color: '#fff', padding: '4px 10px', borderRadius: '6px', fontWeight: 'bold' }} title={isEstimate ? "Estimated score based on Nutri-Score" : "Calculated Scientific Score"}>
            {displayScore.toFixed(1)} / 10
        </span>
    );
}

// --- Parse serving size string into a number ---
function parseServingGrams(servingStr) {
    if (!servingStr) return null;
    // Match patterns like "10g", "10gm", "30 g", "250ml", "250 ml", "1 can (330 ml)"
    const match = servingStr.match(/(\d+\.?\d*)\s*(g|gm|ml|cl|l)\b/i);
    if (!match) return null;
    const val = parseFloat(match[1]);
    const unit = match[2].toLowerCase();
    if (unit === 'cl') return val * 10; // 1cl = 10ml
    if (unit === 'l') return val * 1000;
    return val;
}

// --- Nutrition Panel (Packaging-style table) ---
function NutritionPanel({ nutriments }) {
    const [selectedServing, setSelectedServing] = useState(0);
    const [customGrams, setCustomGrams] = useState('');
    const [isCustom, setIsCustom] = useState(false);

    if (!nutriments || !nutriments.rows || nutriments.rows.length === 0) {
        return (
            <div className="results-card nutrition-panel">
                <h3 className="results-section-title">Nutrition Facts</h3>
                <div className="nutrition-unavailable">
                    <p className="nutrition-unavailable-title">Nutrition data unavailable</p>
                    <p className="nutrition-unavailable-desc">
                        This product does not have nutrition information in our database. Please refer to the product packaging for nutritional values.
                    </p>
                </div>
            </div>
        );
    }

    const rows = nutriments.rows;
    const servingSize = nutriments.serving_size || '';
    const isLiquid = nutriments.is_liquid || false;
    const baseUnit = isLiquid ? 'ml' : 'g';

    // Parse the actual serving size from the product
    const actualServing = parseServingGrams(servingSize);

    // Build serving options dynamically based on product type and actual serving size
    const servingOptions = [];
    if (actualServing && actualServing !== 100) {
        servingOptions.push({ label: `1 Serving (${actualServing}${baseUnit})`, grams: actualServing });
    }
    if (isLiquid) {
        servingOptions.push({ label: '1 Glass (250ml)', grams: 250 });
        servingOptions.push({ label: '1 Can (330ml)', grams: 330 });
    } else {
        servingOptions.push({ label: '50g', grams: 50 });
        servingOptions.push({ label: '1 Bowl (200g)', grams: 200 });
    }

    const amount = isCustom
        ? (parseFloat(customGrams) || 0)
        : servingOptions[selectedServing]?.grams || 100;
    const multiplier = amount / 100;
    const isBaseServing = !isCustom && amount === 100;

    const servingLabel = isCustom
        ? (customGrams ? `Per ${customGrams}${baseUnit}` : 'Per —')
        : `Per ${servingOptions[selectedServing]?.label || '100' + baseUnit}`;

    // Format value based on unit type
    const formatVal = (val, unit) => {
        if (unit === 'kcal' || unit === 'kJ') return Math.round(val);
        if (val < 0.1 && val > 0) return '<0.1';
        return val.toFixed(1);
    };

    return (
        <div className="results-card nutrition-panel">
            <h3 className="results-section-title">Nutrition Facts</h3>

            {servingSize && (
                <p className="nutrition-serving-size">Serving size: {servingSize}</p>
            )}

            {/* Serving Size Selector */}
            <div className="serving-selector">
                {servingOptions.map((option, idx) => (
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
                    <span className="serving-custom-unit">{baseUnit}</span>
                </div>
            </div>

            {/* Nutrition Table */}
            <div className="nutrition-table-wrapper">
                <table className="nutrition-table">
                    <thead>
                        <tr>
                            <th className="nt-label-col">Nutrient</th>
                            <th className="nt-val-col">Per 100{baseUnit}</th>
                            {!isBaseServing && (
                                <th className="nt-val-col nt-serving-col">{servingLabel}</th>
                            )}
                        </tr>
                    </thead>
                    <tbody>
                        {rows.map((row, idx) => (
                            <tr key={idx}>
                                <td className="nt-label">{row.label}</td>
                                <td className="nt-value">{formatVal(row.value, row.unit)} {row.unit}</td>
                                {!isBaseServing && (
                                    <td className="nt-value nt-serving-val">
                                        {amount > 0
                                            ? `${formatVal(row.value * multiplier, row.unit)} ${row.unit}`
                                            : '—'
                                        }
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

// --- Scan History (localStorage) ---
const HISTORY_KEY = 'ingrexa_scan_history';
const MAX_HISTORY = 1000; // Effectively unlimited for local storage

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
    // Limit to a large number to prevent local storage overflow
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
                    {meta.name ? (
                        <div className="product-identity-row">
                            {meta.image_url && (
                                <img src={meta.image_url} alt={meta.name} className="product-identity-img" />
                            )}
                            <div className="product-identity-info">
                                <span className="product-identity-name">{meta.name}</span>
                                {meta.brand && <span className="product-identity-brand">{meta.brand}</span>}
                            </div>
                            <ScoreBadge score={data.score} grade={meta.nutriscore_grade} />
                        </div>
                    ) : (
                        <p style={{ color: 'var(--color-text-tertiary)', fontSize: 'var(--font-size-sm)', marginBottom: 'var(--spacing-md)' }}>
                            Analyzed from manually entered ingredients
                        </p>
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
                                <p className="overview-stat-value">{renderOverviewValue(signal.value)}</p>
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
                                        <ScoreBadge grade={alt.nutriscore_grade} size="small" />
                                    </div>
                                ))}
                            </div>
                        )}
                    </div>
                )}

                {/* SECTION 7: Transparency Note */}
                {data.transparency_note && (
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
                )}

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
