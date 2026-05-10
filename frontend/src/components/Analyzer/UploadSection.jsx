import React, { useState, useRef, useEffect, useCallback } from 'react';
import api from '../../api';

const LOADING_MESSAGES = [
    'Parsing molecular structure...',
    'Cross-referencing global databases...',
    'Identifying synthetic additives...',
    'Evaluating additive synergy...',
    'Finalizing clinical report...',
];

let prefetchStore = { category: null, nutriscore: null, productName: null, data: null };

export const getPrefetchedAlternatives = (category, nutriscore, productName) => {
    const s = prefetchStore;
    if (s.category === category && s.nutriscore === nutriscore && s.productName === productName) {
        return s.data;
    }
    return null;
};

const savePrefetch = (category, nutriscore, productName, data) => {
    prefetchStore = { category, nutriscore, productName, data };
};

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
        const handleClick = (e) => {
            if (dropdownRef.current && !dropdownRef.current.contains(e.target)) {
                setShowDropdown(false);
            }
        };
        document.addEventListener('mousedown', handleClick);
        return () => document.removeEventListener('mousedown', handleClick);
    }, []);

    useEffect(() => {
        if (!isAnalyzing && !isLoading) {
            setMsgIndex(0);
            return;
        }
        const interval = setInterval(() => setMsgIndex(i => (i + 1) % LOADING_MESSAGES.length), 1800);
        return () => clearInterval(interval);
    }, [isAnalyzing, isLoading]);

    useEffect(() => {
        if (user?.health_goal) setUserGoal(user.health_goal);
    }, [user]);

    const searchProducts = useCallback(async (query) => {
        if (abortRef.current) abortRef.current.abort();
        if (!query || query.trim().length < 2) {
            setSearchResults([]);
            setShowDropdown(false);
            return;
        }

        const controller = new AbortController();
        abortRef.current = controller;
        setIsSearching(true);

        try {
            const res = await api.get('/api/search-product/', {
                params: { q: query },
                signal: controller.signal,
            });
            if (res.data.success) {
                setSearchResults(res.data.products || []);
                setShowDropdown(true);
                setSearchError(null);
            }
        } catch (err) {
            if (err.name !== 'CanceledError') {
                const msg = err.response?.status === 429
                    ? 'Searching too fast, please wait a moment.'
                    : 'Search failed. Please try again.';
                setSearchError({ type: err.response?.status === 429 ? 'warning' : 'error', message: msg });
            }
        } finally {
            setIsSearching(false);
        }
    }, []);

    const handleSearchChange = (e) => {
        const val = e.target.value;
        setSearchQuery(val);

        if (!val.trim() || val.trim().length < 2) {
            clearTimeout(searchTimer.current);
            if (abortRef.current) abortRef.current.abort();
            setSearchResults([]);
            setShowDropdown(false);
            return;
        }

        clearTimeout(searchTimer.current);
        searchTimer.current = setTimeout(() => searchProducts(val), 200);
    };

    const handleSearchSubmit = (e) => {
        if (e) e.preventDefault();
        if (searchResults.length > 0) handleAnalyzeProduct(searchResults[0]);
    };

    const handleAnalyzeProduct = async (product) => {
        setSelectedProduct(product);
        setIsAnalyzing(true);
        setShowDropdown(false);

        try {
            const res = await api.post('/api/analyze-product/', {
                barcode: product.barcode,
                user_goal: userGoal,
            });

            if (res.data.success) {
                if (product.categories) {
                    api.get('/api/alternatives/', {
                        params: { category: product.categories, nutriscore: product.nutriscore_grade || '', name: product.name || '' },
                        timeout: 10000,
                    }).then(alt => {
                        if (alt.data.success) savePrefetch(product.categories, product.nutriscore_grade, product.name, alt.data.alternatives);
                    }).catch(() => {});
                }
                onAnalyze(res.data, null);
            } else {
                setError({ title: 'Analysis Error', message: res.data.message });
            }
        } catch {
            setError({ title: 'Connection Error', message: 'Failed to analyze product.' });
        } finally {
            setIsAnalyzing(false);
        }
    };

    const handleManualAnalyze = async () => {
        if (!manualText.trim()) return;
        setIsLoading(true);
        try {
            const res = await api.post('/api/analyze/text/', { text: manualText, user_goal: userGoal });
            if (res.data.success) {
                onAnalyze(res.data, null);
            } else {
                setError({ title: 'Analysis Error', message: res.data.message });
            }
        } catch {
            setError({ title: 'Connection Error', message: 'Failed to analyze ingredients.' });
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <section className="upload-section" id="analyze-section">
            <div className="section-container">
                <div className="analyzer-header">
                    <h2 className="analyzer-title">Molecular Analyzer</h2>
                    <p className="analyzer-subtitle">Analyze ingredients with clinical precision using our proprietary health-scoring algorithm.</p>
                </div>

                <div className="analyzer-tabs">
                    <button className={`analyzer-tab ${activeTab === 'search' ? 'active' : ''}`} onClick={() => setActiveTab('search')}>
                        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5"><circle cx="11" cy="11" r="8"></circle><path d="M21 21l-4.35-4.35"></path></svg>
                        Product Search
                    </button>
                    <button className={`analyzer-tab ${activeTab === 'manual' ? 'active' : ''}`} onClick={() => setActiveTab('manual')}>
                        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5"><path d="M11 4H4a2 2 0 00-2 2v14a2 2 0 002 2h14a2 2 0 002-2v-7"></path><path d="M18.5 2.5a2.121 2.121 0 013 3L12 15l-4 1 1-4 9.5-9.5z"></path></svg>
                        Raw Ingredients
                    </button>
                </div>

                <div className="analyzer-content-wrapper">
                    {activeTab === 'search' && (
                        <div className="upload-box search-active">
                            {isAnalyzing ? (
                                <div className="analysis-overlay">
                                    <div className="analysis-overlay-content">
                                        <div className="zen-loader">
                                            <div className="zen-loader-ring"></div>
                                            <div className="zen-loader-active"></div>
                                        </div>
                                        <div className="analysis-loading-message">
                                            <span className="analysis-msg-text">{LOADING_MESSAGES[msgIndex]}</span>
                                        </div>
                                        {selectedProduct && (
                                            <div className="analysis-product-preview">
                                                <div className="analysis-preview-img-container">
                                                    {selectedProduct.image_url ? (
                                                        <img src={selectedProduct.image_url} alt="" className="analysis-preview-img" />
                                                    ) : (
                                                        <div className="analysis-preview-img-placeholder">
                                                            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"><path d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4" /></svg>
                                                        </div>
                                                    )}
                                                </div>
                                                <div className="analysis-preview-info">
                                                    <p className="analysis-preview-brand">{selectedProduct.brand}</p>
                                                    <p className="analysis-preview-name">{selectedProduct.name}</p>
                                                </div>
                                            </div>
                                        )}
                                    </div>
                                </div>
                            ) : (
                                <>
                                <div className={`search-dropdown-container ${showDropdown ? 'dropdown-open' : ''}`} ref={dropdownRef}>
                                    <form onSubmit={handleSearchSubmit} className="product-search-form">
                                        <div className="search-input-wrapper">
                                            <div className="search-icon">
                                                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5"><circle cx="11" cy="11" r="8"></circle><path d="M21 21l-4.35-4.35"></path></svg>
                                            </div>
                                            <input
                                                ref={searchInputRef}
                                                type="text"
                                                className="premium-search-input"
                                                placeholder="Search for a product... (e.g. Maggi, Parle-G, Amul Butter)"
                                                value={searchQuery}
                                                onChange={handleSearchChange}
                                                onFocus={() => { if (searchQuery.trim().length >= 2) setShowDropdown(true); }}
                                            />
                                            {isSearching && <div className="search-progress-bar"></div>}
                                            {searchQuery && !isSearching && (
                                                <button className="search-clear-btn" type="button" onClick={() => {
                                                    setSearchQuery('');
                                                    setSearchResults([]);
                                                    setShowDropdown(false);
                                                    searchInputRef.current?.focus();
                                                }}>
                                                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5"><path d="M18 6L6 18M6 6l12 12" /></svg>
                                                </button>
                                            )}
                                        </div>
                                    </form>

                                    {showDropdown && (isSearching || searchResults.length > 0) && (
                                        <div className="premium-dropdown">
                                            <div className="dropdown-results">
                                                {isSearching ? (
                                                    <div className="skeleton-container">
                                                        {[1, 2, 3].map(i => (
                                                            <div key={i} className="skeleton-item">
                                                                <div className="skeleton-img shimmer"></div>
                                                                <div className="skeleton-text-group">
                                                                    <div className="skeleton-title shimmer"></div>
                                                                    <div className="skeleton-subtitle shimmer"></div>
                                                                </div>
                                                            </div>
                                                        ))}
                                                    </div>
                                                ) : (
                                                    searchResults.map((product, idx) => (
                                                        <button key={product.barcode || idx} className="dropdown-item" onClick={() => handleAnalyzeProduct(product)}>
                                                            <div className="item-search-icon">
                                                                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="11" cy="11" r="8"></circle><path d="M21 21l-4.35-4.35"></path></svg>
                                                            </div>
                                                            <div className="item-info">
                                                                <span className="item-name">{product.name}</span>
                                                                <span className="item-brand">{product.brand}</span>
                                                            </div>
                                                            <div className="item-img">
                                                                {product.image_url ? (
                                                                    <img src={product.image_url} alt="" />
                                                                ) : (
                                                                    <div className="img-placeholder"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor"><path d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4" /></svg></div>
                                                                )}
                                                            </div>
                                                            <div className="item-action">
                                                                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5"><path d="M5 12h14M12 5l7 7-7 7" /></svg>
                                                            </div>
                                                        </button>
                                                    ))
                                                )}
                                            </div>
                                        </div>
                                    )}
                                </div>

                                {!searchQuery && (
                                    <div className="search-onboarding">
                                        <p className="onboarding-label">Suggested Samples</p>
                                        <div className="onboarding-chips">
                                            {['Maggi', 'Parle-G', 'Amul', 'Haldiram', 'Britannia', 'Kurkure'].map((term) => (
                                                <button key={term} className="onboarding-chip" onClick={() => { setSearchQuery(term); searchProducts(term); }}>
                                                    {term}
                                                </button>
                                            ))}
                                        </div>
                                    </div>
                                )}
                                </>
                            )}
                        </div>
                    )}

                    {activeTab === 'manual' && (
                        <div className="upload-box manual-active">
                            {isLoading ? (
                                <div className="analysis-overlay">
                                    <div className="analysis-overlay-content">
                                        <div className="premium-scanner">
                                            <svg className="scanner-svg" viewBox="0 0 100 100">
                                                <circle className="scanner-track" cx="50" cy="50" r="45" />
                                                <circle className="scanner-beam" cx="50" cy="50" r="45" />
                                                <path className="scanner-shield" d="M50 30 L65 37 V50 C65 60 50 68 50 68 C50 68 35 60 35 50 V37 L50 30 Z" />
                                            </svg>
                                            <div className="scanner-glow"></div>
                                        </div>
                                        <div className="analysis-loading-message">
                                            <span className="analysis-msg-text">{LOADING_MESSAGES[msgIndex]}</span>
                                        </div>
                                    </div>
                                </div>
                            ) : (
                                <>
                                    <textarea
                                        className="premium-textarea"
                                        placeholder="Paste clinical ingredient data here..."
                                        value={manualText}
                                        onChange={(e) => setManualText(e.target.value)}
                                    ></textarea>
                                    <button
                                        className="btn-ultra-primary analyze-btn"
                                        onClick={handleManualAnalyze}
                                        disabled={!manualText.trim()}
                                    >
                                        Run Molecular Analysis
                                        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5"><path d="M5 12h14M12 5l7 7-7 7" /></svg>
                                    </button>
                                    <p className="clinical-hint">Ensure all additives and preservation agents are included for accurate scoring.</p>
                                </>
                            )}
                        </div>
                    )}
                </div>
            </div>

            {error && (
                <div className="validation-error-toast" onClick={() => setError(null)}>
                    <div className="toast-content">
                        <strong>{error.title}</strong>
                        <p>{error.message}</p>
                    </div>
                </div>
            )}
        </section>
    );
}

export default UploadSection;
