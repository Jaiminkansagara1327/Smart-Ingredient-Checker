import React, { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import api from '../../api';
import { getPrefetchedAlternatives } from './UploadSection';

const RED_FLAGS = ['palm oil','partially hydrogenated','hydrogenated','high fructose corn syrup','msg','monosodium glutamate','sodium benzoate','potassium sorbate','aspartame','sucralose','acesulfame','saccharin','artificial','synthetic','tbhq','bha','bht','sodium nitrite','sodium nitrate','propyl gallate','carrageenan','polysorbate','titanium dioxide','tartrazine','sunset yellow','brilliant blue','allura red','caramel color','caramel colour'];
const GREEN_FLAGS = ['whole wheat','whole grain','oats','fiber','fibre','olive oil','flaxseed','chia','quinoa','turmeric','ginger','garlic','cinnamon','vitamin','mineral','iron','calcium','zinc','probiotic','prebiotic','antioxidant','organic','natural flavor','natural flavour','honey','jaggery','coconut oil','millets'];
const E_NUMBER = /\b(e|ins)\s*\d{3,4}[a-z]?\b/gi;

function stripEmojis(text) {
  if (!text) return '';
  return text.replace(/[\u{1F300}-\u{1F9FF}]|[\u{2600}-\u{26FF}]/gu, '').trim();
}

function renderValue(val) {
  if (!val) return 'Unknown';
  const s = String(val).trim();
  if (['not applicable', 'unknown'].includes(s.toLowerCase())) return <span style={{ color: 'var(--text-tertiary)' }}>Unknown</span>;
  return s;
}

function parseServingGrams(str) {
  if (!str) return null;
  const match = str.match(/(\d+\.?\d*)\s*(g|gm|ml|cl|l)\b/i);
  if (!match) return null;
  const val = parseFloat(match[1]); const unit = match[2].toLowerCase();
  if (unit === 'cl') return val * 10; if (unit === 'l') return val * 1000;
  return val;
}

function ScoreArc({ score, grade }) {
  const val = (() => {
    if (score !== undefined) { let v = Number(score); return v > 10 ? v / 10 : v; }
    if (grade) {
      const g = grade.toLowerCase().trim();
      if (g === 'unknown' || g === 'not-applicable' || g.length > 1) return null;
      return { a: 9, b: 7, c: 5, d: 3, e: 1 }[g] || 0;
    }
    return null;
  })();

  if (val === null) return <span style={{ fontSize: 'var(--text-xs)', color: 'var(--text-tertiary)', background: 'var(--surface-3)', padding: '4px 10px', borderRadius: 'var(--radius-full)' }}>NO SCORE</span>;

  const pct = val / 10;
  const r = 30; const circ = 2 * Math.PI * r;
  const offset = circ * (1 - pct);
  const color = val >= 8 ? 'var(--brand-success)' : val >= 5 ? 'var(--brand-warning)' : 'var(--brand-danger)';
  const cls = val >= 8 ? 'high' : val >= 5 ? 'mid' : 'low';

  return (
    <div className="score-wrap">
      <div className="score-circle">
        <svg width="80" height="80" className="score-svg" viewBox="0 0 80 80">
          <circle className="score-track" cx="40" cy="40" r={r} />
          <motion.circle
            className={`score-fill ${cls}`} cx="40" cy="40" r={r}
            strokeDasharray={circ}
            strokeDashoffset={offset}
            style={{ stroke: color }}
            initial={{ strokeDashoffset: circ }}
            animate={{ strokeDashoffset: offset }}
            transition={{ duration: 1.2, ease: [0.16, 1, 0.3, 1], delay: 0.3 }}
          />
        </svg>
        <motion.span
          className="score-num"
          initial={{ opacity: 0, scale: 0.6 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.5, duration: 0.4, ease: [0.16, 1, 0.3, 1] }}
          style={{ color }}
        >
          {val.toFixed(1)}
        </motion.span>
      </div>
      <div className="score-label">/ 10</div>
    </div>
  );
}

function NutritionPanel({ nutriments }) {
  const [selectedServing, setSelectedServing] = useState(0);
  const [customGrams, setCustomGrams] = useState('');
  const [isCustom, setIsCustom] = useState(false);

  if (!nutriments?.rows?.length) {
    return (
      <div className="nutrition-card result-card" style={{ padding: 0 }}>
        <div className="result-card-title" style={{ padding: 'var(--space-5) var(--space-6)', borderBottom: '1px solid var(--border-subtle)', marginBottom: 0 }}>
          <span className="result-card-icon">📊</span> Nutrition Facts
        </div>
        <div className="nutrition-na">
          <p style={{ color: 'var(--text-tertiary)' }}>Nutrition data unavailable.</p>
          <p style={{ fontSize: 'var(--text-xs)', marginTop: 4 }}>Refer to product packaging for nutritional values.</p>
        </div>
      </div>
    );
  }

  const { rows, serving_size: servingSize = '', is_liquid: isLiquid = false } = nutriments;
  const baseUnit = isLiquid ? 'ml' : 'g';
  const actualServing = parseServingGrams(servingSize);
  const options = [];
  if (actualServing && actualServing !== 100) options.push({ label: `1 Serving (${actualServing}${baseUnit})`, grams: actualServing });
  if (isLiquid) { options.push({ label: '1 Glass (250ml)', grams: 250 }); options.push({ label: '1 Can (330ml)', grams: 330 }); }
  else { options.push({ label: '50g', grams: 50 }); options.push({ label: '1 Bowl (200g)', grams: 200 }); }

  const amount = isCustom ? (parseFloat(customGrams) || 0) : options[selectedServing]?.grams || 100;
  const multiplier = amount / 100;
  const isBase = !isCustom && amount === 100;
  const servingLabel = isCustom ? (customGrams ? `Per ${customGrams}${baseUnit}` : 'Per —') : `Per ${options[selectedServing]?.label || '100' + baseUnit}`;
  const fmt = (val, unit) => { if (unit === 'kcal' || unit === 'kJ') return Math.round(val); if (val < 0.1 && val > 0) return '<0.1'; return val.toFixed(1); };

  return (
    <div className="nutrition-card result-card" style={{ padding: 0 }}>
      <div className="result-card-title" style={{ padding: 'var(--space-5) var(--space-6)', borderBottom: '1px solid var(--border-subtle)', marginBottom: 0 }}>
        <span className="result-card-icon">📊</span> Nutrition Facts
        {servingSize && <span style={{ fontSize: 'var(--text-xs)', color: 'var(--text-tertiary)', fontWeight: 400, marginLeft: 'auto' }}>Serving: {servingSize}</span>}
      </div>
      <div className="serving-selector">
        {options.map((opt, idx) => (
          <button key={opt.label} className={`serving-btn ${!isCustom && idx === selectedServing ? 'active' : ''}`} onClick={() => { setSelectedServing(idx); setIsCustom(false); }}>
            {opt.label}
          </button>
        ))}
        <div className={`serving-btn serving-custom ${isCustom ? 'active' : ''}`} onClick={() => setIsCustom(true)}>
          <input type="number" className="serving-custom" placeholder="Custom" min="1" max="5000" value={customGrams} onFocus={() => setIsCustom(true)} onChange={e => { setCustomGrams(e.target.value); setIsCustom(true); }} onClick={e => e.stopPropagation()} style={{ width: 60, background: 'none', border: 'none', outline: 'none', fontSize: 'var(--text-xs)', color: 'var(--text-primary)', textAlign: 'center', fontFamily: 'inherit' }} />
          <span style={{ fontSize: 'var(--text-xs)', color: 'var(--text-tertiary)' }}>{baseUnit}</span>
        </div>
      </div>
      <div className="nutrition-table-wrap">
        <table className="nutrition-table">
          <thead><tr><th>Nutrient</th><th style={{ textAlign: 'right' }}>Per 100{baseUnit}</th>{!isBase && <th style={{ textAlign: 'right' }}>{servingLabel}</th>}</tr></thead>
          <tbody>
            {rows.map((row, idx) => (
              <tr key={idx}>
                <td>{row.label}</td>
                <td style={{ textAlign: 'right' }}>{fmt(row.value, row.unit)} {row.unit}</td>
                {!isBase && <td style={{ textAlign: 'right' }}>{amount > 0 ? `${fmt(row.value * multiplier, row.unit)} ${row.unit}` : '—'}</td>}
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
    filtered.unshift({ name: product.name, brand: product.brand || '', image_url: product.image_url || '', barcode: product.barcode || '', nutriscore_grade: product.nutriscore_grade || '', scannedAt: new Date().toISOString() });
    localStorage.setItem(HISTORY_KEY, JSON.stringify(filtered.slice(0, 1000)));
  } catch {}
}

function getRisk(risk) {
  if (risk === '🔴') return 'high';
  if (risk === '🟡') return 'mod';
  if (risk === '🟢') return 'low';
  return 'neutral';
}

function ResultsSection({ data, image, onAnalyzeNew, onNavigate }) {
  const [expandedIdx, setExpandedIdx] = useState(null);
  if (!data) return null;

  const hasFormat = data.overview && data.frequency_verdict && data.ingredient_breakdown;
  const meta = data._product_meta || {};

  useEffect(() => { if (meta.name) addToHistory(meta); }, [meta.name]);

  if (!hasFormat) return (
    <div style={{ textAlign: 'center', padding: '4rem', color: 'var(--text-secondary)' }}>
      <p>Analysis format not recognized. Please re-analyze.</p>
    </div>
  );

  return (
    <section>
      <div className="results-page">
        {/* Product Hero */}
        <motion.div className="product-hero-card" initial={{ opacity: 0, y: 32 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.6, ease: [0.16, 1, 0.3, 1] }}>
          <div className="product-hero-top">
            {meta.name ? (
              <>
                {meta.image_url && (
                  <div className="product-img-wrap"><img src={meta.image_url} alt={meta.name} /></div>
                )}
                <div className="product-hero-info">
                  <div className="product-brand">{meta.brand || 'Unknown Brand'}</div>
                  <h2 className="product-name">{meta.name}</h2>
                  {data.details?.goal_used && (
                    <div className="product-badges">
                      <span className="product-badge">🎯 {data.details.goal_used}</span>
                      <span className="product-badge">🥣 {data.details.type_used}</span>
                    </div>
                  )}
                </div>
              </>
            ) : (
              <div className="product-hero-info">
                <div className="product-brand">Manual Analysis</div>
                <h2 className="product-name">Custom Ingredients</h2>
                {data.details?.goal_used && (
                  <div className="product-badges">
                    <span className="product-badge">🎯 {data.details.goal_used}</span>
                  </div>
                )}
              </div>
            )}
            <ScoreArc score={data.score} grade={meta.nutriscore_grade} />
          </div>
          <div className="stats-strip">
            {[
              { label: 'Processing', val: renderValue(data.overview.processing_level) },
              { label: 'Ingredients', val: renderValue(data.overview.ingredient_count) },
              { label: 'Additives', val: renderValue(data.overview.additives_present) },
            ].map(s => (
              <div key={s.label} className="stat-item">
                <div className="stat-item-label">{s.label}</div>
                <div className="stat-item-val">{s.val}</div>
              </div>
            ))}
          </div>
        </motion.div>

        {/* Verdict */}
        <motion.div className="verdict-card" initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.15, duration: 0.5 }}>
          <div className="result-card-title"><span className="result-card-icon">📋</span> AI Verdict</div>
          <p className="verdict-text">{stripEmojis(data.frequency_verdict)}</p>
        </motion.div>

        {/* Key Signals */}
        <motion.div className="result-card" initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2, duration: 0.5 }}>
          <div className="result-card-title"><span className="result-card-icon">⚠️</span> Key Signals</div>
          <div className="signals-grid">
            {[
              { label: 'Added Sugar', value: data.key_signals.added_sugar },
              { label: 'Refined Flour', value: data.key_signals.refined_flour_starch },
              { label: 'Artificial Colors', value: data.key_signals.artificial_colors },
              { label: 'Preservatives', value: data.key_signals.preservatives },
              { label: 'Artificial Flavors', value: data.key_signals.artificial_flavors },
            ].map((s, idx) => {
              const v = String(s.value || '').toLowerCase();
              const cls = v.includes('yes') || v.includes('high') ? 'danger' : v.includes('no') || v.includes('none') ? 'success' : '';
              return (
                <motion.div
                  key={idx} className="signal-card"
                  initial={{ opacity: 0, scale: 0.9 }} animate={{ opacity: 1, scale: 1 }}
                  transition={{ delay: 0.25 + idx * 0.06, duration: 0.35 }}
                >
                  <div className="signal-label">{s.label}</div>
                  <div className={`signal-val ${cls}`}>{renderValue(s.value)}</div>
                </motion.div>
              );
            })}
          </div>
        </motion.div>

        {/* Nutrition */}
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.3, duration: 0.5 }}>
          <NutritionPanel nutriments={meta.nutriments} />
        </motion.div>

        {/* Ingredients */}
        <motion.div className="result-card" initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.35, duration: 0.5 }}>
          <div className="result-card-title"><span className="result-card-icon">🧬</span> Ingredient Intelligence</div>
          <div className="ingredient-legend">
            <span className="legend-dot"><span className="legend-pip red" /> Concern</span>
            <span className="legend-dot"><span className="legend-pip green" /> Healthful</span>
            <span className="legend-dot"><span className="legend-pip warn" /> Caution</span>
            <span className="legend-dot"><span className="legend-pip neutral" /> Neutral</span>
          </div>
          <div>
            {data.ingredient_breakdown.map((item, idx) => {
              const riskKey = getRisk(item.risk);
              const isOpen = expandedIdx === idx;
              const nameCls = riskKey === 'high' || riskKey === 'mod' ? 'flagged' : riskKey === 'low' ? 'good' : '';
              return (
                <div key={idx}>
                  <motion.div
                    className={`ingredient-row ${isOpen ? 'open' : ''}`}
                    onClick={() => setExpandedIdx(isOpen ? null : idx)}
                    whileHover={{ backgroundColor: 'var(--surface-glass-hover)' }}
                  >
                    <span className={`risk-pip ${riskKey}`} />
                    <span className={`ing-name ${nameCls}`}>{item.name}</span>
                    <span className="ing-role">{item.role}</span>
                    <motion.span className="ing-expand" animate={{ rotate: isOpen ? 180 : 0 }} transition={{ duration: 0.2 }}>
                      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5"><polyline points="6 9 12 15 18 9" /></svg>
                    </motion.span>
                  </motion.div>
                  <AnimatePresence>
                    {isOpen && (
                      <motion.div
                        className="ingredient-detail"
                        initial={{ opacity: 0, height: 0 }}
                        animate={{ opacity: 1, height: 'auto' }}
                        exit={{ opacity: 0, height: 0 }}
                        transition={{ duration: 0.22 }}
                        style={{ overflow: 'hidden' }}
                      >
                        {item.description || 'Common food component with no notable concerns.'}
                      </motion.div>
                    )}
                  </AnimatePresence>
                </div>
              );
            })}
          </div>
        </motion.div>

        {/* Transparency note */}
        {data.transparency_note && (
          <p style={{ textAlign: 'center', fontSize: 'var(--text-xs)', color: 'var(--text-tertiary)', fontStyle: 'italic', lineHeight: 1.6, padding: 'var(--space-4) 0' }}>
            {data.transparency_note}
          </p>
        )}

        {/* Analyze Another */}
        <motion.button
          className="analyze-again-btn"
          onClick={onAnalyzeNew}
          whileHover={{ scale: 1.01 }} whileTap={{ scale: 0.99 }}
        >
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
            <polyline points="23 4 23 10 17 10" /><polyline points="1 20 1 14 7 14" />
            <path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15" />
          </svg>
          Analyze Another Product
        </motion.button>
      </div>
    </section>
  );
}

export default ResultsSection;
