import React, { useState, useRef, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import api from '../../api';

const LOADING_MESSAGES = [
  'Parsing molecular structure…',
  'Cross-referencing global databases…',
  'Identifying synthetic additives…',
  'Evaluating additive synergy…',
  'Finalizing clinical report…',
];

let prefetchStore = { category: null, nutriscore: null, productName: null, data: null };
export const getPrefetchedAlternatives = (category, nutriscore, productName) => {
  const s = prefetchStore;
  if (s.category === category && s.nutriscore === nutriscore && s.productName === productName) return s.data;
  return null;
};
const savePrefetch = (category, nutriscore, productName, data) => {
  prefetchStore = { category, nutriscore, productName, data };
};

const SearchIcon = () => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
    <circle cx="11" cy="11" r="8" /><path d="M21 21l-4.35-4.35" />
  </svg>
);
const PenIcon = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
    <path d="M11 4H4a2 2 0 00-2 2v14a2 2 0 002 2h14a2 2 0 002-2v-7" /><path d="M18.5 2.5a2.121 2.121 0 013 3L12 15l-4 1 1-4 9.5-9.5z" />
  </svg>
);
const XIcon = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
    <path d="M18 6L6 18M6 6l12 12" />
  </svg>
);
const ArrowIcon = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
    <path d="M5 12h14M12 5l7 7-7 7" />
  </svg>
);
const BoxIcon = () => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
    <path d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4" />
  </svg>
);

const CHIPS = ['Maggi', 'Parle-G', 'Amul', 'Haldiram', 'Britannia', 'Kurkure', 'Bournvita', 'Lays'];

function UploadSection({ onAnalyze, user }) {
  const [activeTab, setActiveTab] = useState('search');
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [isSearching, setIsSearching] = useState(false);
  const [searchError, setSearchError] = useState(null);
  const [selectedProduct, setSelectedProduct] = useState(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [msgIndex, setMsgIndex] = useState(0);
  const [manualText, setManualText] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [userGoal, setUserGoal] = useState('Regular');
  const [showDropdown, setShowDropdown] = useState(false);

  const searchTimer = useRef(null);
  const searchInputRef = useRef(null);
  const dropdownRef = useRef(null);
  const abortRef = useRef(null);

  useEffect(() => {
    const handler = (e) => { if (dropdownRef.current && !dropdownRef.current.contains(e.target)) setShowDropdown(false); };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, []);

  useEffect(() => {
    if (!isAnalyzing && !isLoading) { setMsgIndex(0); return; }
    const iv = setInterval(() => setMsgIndex(i => (i + 1) % LOADING_MESSAGES.length), 1800);
    return () => clearInterval(iv);
  }, [isAnalyzing, isLoading]);

  useEffect(() => { if (user?.health_goal) setUserGoal(user.health_goal); }, [user]);

  const searchProducts = useCallback(async (query) => {
    if (abortRef.current) abortRef.current.abort();
    if (!query || query.trim().length < 2) { setSearchResults([]); setShowDropdown(false); return; }
    const controller = new AbortController();
    abortRef.current = controller;
    setIsSearching(true);
    try {
      const res = await api.get('/api/search-product/', { params: { q: query }, signal: controller.signal });
      if (res.data.success) { setSearchResults(res.data.products || []); setShowDropdown(true); setSearchError(null); }
    } catch (err) {
      if (err.name !== 'CanceledError') {
        const msg = err.response?.status === 429 ? 'Searching too fast, please wait.' : 'Search failed. Please try again.';
        setSearchError({ type: err.response?.status === 429 ? 'warning' : 'error', message: msg });
      }
    } finally { setIsSearching(false); }
  }, []);

  const handleSearchChange = (e) => {
    const val = e.target.value;
    setSearchQuery(val);
    if (!val.trim() || val.trim().length < 2) { clearTimeout(searchTimer.current); if (abortRef.current) abortRef.current.abort(); setSearchResults([]); setShowDropdown(false); return; }
    clearTimeout(searchTimer.current);
    searchTimer.current = setTimeout(() => searchProducts(val), 220);
  };

  const handleAnalyzeProduct = async (product) => {
    setSelectedProduct(product); setIsAnalyzing(true); setShowDropdown(false);
    try {
      const res = await api.post('/api/analyze-product/', { barcode: product.barcode, user_goal: userGoal });
      if (res.data.success) {
        if (product.categories) {
          api.get('/api/alternatives/', { params: { category: product.categories, nutriscore: product.nutriscore_grade || '', name: product.name || '' }, timeout: 10000 })
            .then(alt => { if (alt.data.success) savePrefetch(product.categories, product.nutriscore_grade, product.name, alt.data.alternatives); })
            .catch(() => {});
        }
        onAnalyze(res.data, null);
      } else { setError({ title: 'Analysis Error', message: res.data.message }); }
    } catch { setError({ title: 'Connection Error', message: 'Failed to analyze product.' }); }
    finally { setIsAnalyzing(false); }
  };

  const handleManualAnalyze = async () => {
    if (!manualText.trim()) return;
    setIsLoading(true);
    try {
      const res = await api.post('/api/analyze/text/', { text: manualText, user_goal: userGoal });
      if (res.data.success) onAnalyze(res.data, null);
      else setError({ title: 'Analysis Error', message: res.data.message });
    } catch { setError({ title: 'Connection Error', message: 'Failed to analyze ingredients.' }); }
    finally { setIsLoading(false); }
  };

  const isLoaderVisible = isAnalyzing || isLoading;

  return (
    <section style={{ minHeight: 'calc(100dvh - var(--header-h))', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
      <div className="analyzer-page" style={{ width: '100%' }}>
        {/* Header */}
        <motion.div className="analyzer-header" initial={{ opacity: 0, y: 24 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.6, ease: [0.16, 1, 0.3, 1] }}>
          <div className="analyzer-eyebrow"><span>🔬</span> Molecular Analyzer</div>
          <h2 className="analyzer-title">What's really in your food?</h2>
          <p className="analyzer-sub">Search any Indian packaged product or paste ingredients for instant AI analysis.</p>
        </motion.div>

        {/* Tabs */}
        <motion.div className="analyzer-tabs" initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5, delay: 0.1 }}>
          <button className={`tab-btn ${activeTab === 'search' ? 'active' : ''}`} onClick={() => setActiveTab('search')}>
            <SearchIcon /> Product Search
          </button>
          <button className={`tab-btn ${activeTab === 'manual' ? 'active' : ''}`} onClick={() => setActiveTab('manual')}>
            <PenIcon /> Raw Ingredients
          </button>
        </motion.div>

        <AnimatePresence mode="wait">
          {/* ── SEARCH TAB ── */}
          {activeTab === 'search' && (
            <motion.div key="search" initial={{ opacity: 0, x: -16 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: 16 }} transition={{ duration: 0.25 }}>
              {isLoaderVisible ? (
                <div className="search-panel">
                  <div className="analyze-overlay">
                    <div className="loader-ring" />
                    <AnimatePresence mode="wait">
                      <motion.p key={msgIndex} className="loader-msg" initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -8 }} transition={{ duration: 0.3 }}>
                        {LOADING_MESSAGES[msgIndex]}
                      </motion.p>
                    </AnimatePresence>
                    {selectedProduct && (
                      <div className="loader-product-preview">
                        {selectedProduct.image_url ? (
                          <img src={selectedProduct.image_url} alt="" className="loader-product-img" />
                        ) : (
                          <div className="loader-product-img" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--text-tertiary)' }}><BoxIcon /></div>
                        )}
                        <div>
                          <div className="loader-product-brand">{selectedProduct.brand}</div>
                          <div className="loader-product-name">{selectedProduct.name}</div>
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              ) : (
                <div className="search-panel" ref={dropdownRef}>
                  <div className="search-bar-wrap">
                    <div className="search-bar">
                      <span className="search-bar-icon"><SearchIcon /></span>
                      <input
                        ref={searchInputRef}
                        type="text"
                        className="search-input"
                        placeholder="Search Maggi, Parle-G, Amul Butter…"
                        value={searchQuery}
                        onChange={handleSearchChange}
                        onFocus={() => { if (searchQuery.trim().length >= 2) setShowDropdown(true); }}
                        autoFocus
                      />
                      {searchQuery && !isSearching && (
                        <button className="search-clear" type="button" onClick={() => { setSearchQuery(''); setSearchResults([]); setShowDropdown(false); searchInputRef.current?.focus(); }}>
                          <XIcon />
                        </button>
                      )}
                    </div>
                    {isSearching && (
                      <div className="search-progress">
                        <div style={{ position: 'absolute', inset: 0, background: 'var(--gradient-brand)', backgroundSize: '200% 100%', animation: 'shimmer 1.2s infinite linear', borderRadius: 'inherit' }} />
                      </div>
                    )}
                  </div>

                  <AnimatePresence>
                    {showDropdown && (isSearching || searchResults.length > 0) && (
                      <motion.div
                        className="results-dropdown"
                        initial={{ opacity: 0, height: 0 }}
                        animate={{ opacity: 1, height: 'auto' }}
                        exit={{ opacity: 0, height: 0 }}
                        transition={{ duration: 0.2 }}
                        style={{ overflow: 'hidden' }}
                      >
                        {isSearching ? (
                          [1, 2, 3].map(i => (
                            <div key={i} className="skeleton-row">
                              <div className="skeleton skeleton-img-sq" style={{ height: 44, width: 44, borderRadius: 'var(--radius-md)' }} />
                              <div className="skeleton-text-col">
                                <div className="skeleton skeleton-line" style={{ height: 13 }} />
                                <div className="skeleton skeleton-line short" style={{ height: 11, marginTop: 6 }} />
                              </div>
                            </div>
                          ))
                        ) : (
                          searchResults.map((product, idx) => (
                            <motion.button
                              key={product.barcode || idx}
                              className="dropdown-item-btn"
                              onClick={() => handleAnalyzeProduct(product)}
                              initial={{ opacity: 0, x: -8 }}
                              animate={{ opacity: 1, x: 0 }}
                              transition={{ delay: idx * 0.04 }}
                            >
                              <div className="dropdown-item-img">
                                {product.image_url ? <img src={product.image_url} alt="" /> : <BoxIcon />}
                              </div>
                              <div className="dropdown-item-text">
                                <div className="dropdown-item-name">{product.name}</div>
                                <div className="dropdown-item-brand">{product.brand}</div>
                              </div>
                              <div className="dropdown-item-arrow"><ArrowIcon /></div>
                            </motion.button>
                          ))
                        )}
                      </motion.div>
                    )}
                  </AnimatePresence>

                  {!searchQuery && (
                    <div className="chips-section">
                      <div className="chips-label">Suggested Samples</div>
                      <div className="chips-row">
                        {CHIPS.map(term => (
                          <motion.button
                            key={term} className="chip"
                            onClick={() => { setSearchQuery(term); searchProducts(term); }}
                            whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }}
                          >
                            {term}
                          </motion.button>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )}
            </motion.div>
          )}

          {/* ── MANUAL TAB ── */}
          {activeTab === 'manual' && (
            <motion.div key="manual" initial={{ opacity: 0, x: 16 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -16 }} transition={{ duration: 0.25 }}>
              <div className="manual-panel">
                {isLoaderVisible ? (
                  <div className="analyze-overlay">
                    <div className="loader-ring" />
                    <AnimatePresence mode="wait">
                      <motion.p key={msgIndex} className="loader-msg" initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -8 }} transition={{ duration: 0.3 }}>
                        {LOADING_MESSAGES[msgIndex]}
                      </motion.p>
                    </AnimatePresence>
                  </div>
                ) : (
                  <>
                    <textarea
                      className="manual-textarea"
                      placeholder="Paste ingredient list here…&#10;e.g. Sugar, Wheat Flour, Palm Oil, E150c, INS 503(ii), Salt, Natural Vanilla, Synthetic Flavour"
                      value={manualText}
                      onChange={e => setManualText(e.target.value)}
                    />
                    <div className="manual-footer">
                      <span className="manual-hint">💡 Include all additives for accurate scoring.</span>
                      <motion.button
                        className="btn-primary"
                        onClick={handleManualAnalyze}
                        disabled={!manualText.trim()}
                        style={{ fontSize: 'var(--text-sm)', padding: 'var(--space-3) var(--space-6)' }}
                        whileHover={{ scale: 1.03 }} whileTap={{ scale: 0.97 }}
                      >
                        Run Analysis
                        <ArrowIcon />
                      </motion.button>
                    </div>
                  </>
                )}
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Error toast */}
      <AnimatePresence>
        {error && (
          <motion.div
            className="error-toast"
            initial={{ opacity: 0, y: 24 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 24 }}
            onClick={() => setError(null)}
          >
            <div className="error-toast-title">{error.title}</div>
            <div className="error-toast-msg">{error.message}</div>
          </motion.div>
        )}
      </AnimatePresence>
    </section>
  );
}

export default UploadSection;
