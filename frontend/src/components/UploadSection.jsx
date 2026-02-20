import React, { useState, useRef, useEffect, useCallback } from 'react';
import api from '../api';

// Smart loading messages shown during analysis
const ANALYSIS_MESSAGES = [
    { icon: '🔬', text: 'Reading ingredient list...' },
    { icon: '🧪', text: 'Checking for harmful additives...' },
    { icon: '📊', text: 'Calculating health score...' },
    { icon: '⚠️', text: 'Identifying allergens & warnings...' },
    { icon: '✅', text: 'Preparing your report...' },
];

// =========== FRONTEND SEARCH CACHE ===========
// In-memory cache for instant repeat lookups (survives within session)
const _searchCache = new Map();
const SEARCH_CACHE_TTL = 5 * 60 * 1000; // 5 minutes
const SEARCH_CACHE_MAX = 100;

function getCachedSearch(query) {
    const key = query.trim().toLowerCase();
    const entry = _searchCache.get(key);
    if (entry && Date.now() - entry.ts < SEARCH_CACHE_TTL) return entry.data;
    if (entry) _searchCache.delete(key);
    return null;
}

function setCachedSearch(query, data) {
    const key = query.trim().toLowerCase();
    if (_searchCache.size >= SEARCH_CACHE_MAX) {
        // Evict oldest
        const firstKey = _searchCache.keys().next().value;
        _searchCache.delete(firstKey);
    }
    _searchCache.set(key, { ts: Date.now(), data });
}

// =========== ALTERNATIVES PREFETCH CACHE ===========
// Prefetch alternatives during analysis so they load instantly on results page
const _altCache = new Map();

function getPrefetchedAlternatives(categories, nutriscore, name) {
    const key = `${categories}|${nutriscore}|${name}`;
    return _altCache.get(key) || null;
}

function setPrefetchedAlternatives(categories, nutriscore, name, data) {
    const key = `${categories}|${nutriscore}|${name}`;
    _altCache.set(key, data);
}

function UploadSection({ onAnalyze }) {
    // Tab state: 'search' or 'manual'
    const [activeTab, setActiveTab] = useState('search');

    // Search state
    const [searchQuery, setSearchQuery] = useState('');
    const [searchResults, setSearchResults] = useState([]);
    const [isSearching, setIsSearching] = useState(false);
    const [searchError, setSearchError] = useState(null);
    const [selectedProduct, setSelectedProduct] = useState(null);
    const [isAnalyzingProduct, setIsAnalyzingProduct] = useState(false);
    const [loadingMsgIndex, setLoadingMsgIndex] = useState(0);
    const [showHistoryModal, setShowHistoryModal] = useState(false);

    // Manual text state
    const [manualText, setManualText] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [validationError, setValidationError] = useState(null);

    // Dropdown open/close
    const [showDropdown, setShowDropdown] = useState(false);

    // Debounce timer ref
    const searchTimerRef = useRef(null);
    const searchInputRef = useRef(null);
    const dropdownRef = useRef(null);
    const abortControllerRef = useRef(null);  // Cancel stale API requests
    const searchQueryRef = useRef('');  // Track current query to ignore stale responses

    // Click outside to close dropdown
    useEffect(() => {
        const handleClickOutside = (e) => {
            if (dropdownRef.current && !dropdownRef.current.contains(e.target)) {
                setShowDropdown(false);
            }
        };
        document.addEventListener('mousedown', handleClickOutside);
        return () => document.removeEventListener('mousedown', handleClickOutside);
    }, []);

    // Rotate loading messages during analysis
    useEffect(() => {
        if (!isAnalyzingProduct && !isLoading) {
            setLoadingMsgIndex(0);
            return;
        }
        const interval = setInterval(() => {
            setLoadingMsgIndex(prev => (prev + 1) % ANALYSIS_MESSAGES.length);
        }, 1800);
        return () => clearInterval(interval);
    }, [isAnalyzingProduct, isLoading]);

    // ========================================
    //  SEARCH TAB LOGIC
    // ========================================

    const searchProducts = useCallback(async (query) => {
        if (!query || query.trim().length < 2) {
            setSearchResults([]);
            setSearchError(null);
            setIsSearching(false);
            setShowDropdown(false);
            return;
        }

        // Cancel any in-flight request
        if (abortControllerRef.current) {
            abortControllerRef.current.abort();
        }

        const controller = new AbortController();
        abortControllerRef.current = controller;
        const thisQuery = query.trim();
        searchQueryRef.current = thisQuery;

        setSearchError(null);

        // ⚡ Check frontend cache FIRST — instant results
        const cached = getCachedSearch(thisQuery);
        if (cached) {
            setSearchResults(cached.products || []);
            setShowDropdown(true);
            setIsSearching(false);
            if ((cached.products || []).length === 0) {
                setSearchError({
                    type: 'no_results',
                    message: `No products found for "${query}". Try a different name or use the "Type Ingredients" tab.`
                });
            }
            return;
        }

        setIsSearching(true);

        try {
            const response = await api.get('/api/search-product/', {
                params: { q: thisQuery },
                signal: controller.signal,
                timeout: 15000, // Generous timeout for slow connections
            });

            // Ignore if query changed while waiting (stale response)
            if (searchQueryRef.current !== thisQuery) return;

            if (response.data.success) {
                setSearchResults(response.data.products || []);
                setShowDropdown(true);
                // ⚡ Cache the result for instant future lookups
                setCachedSearch(thisQuery, response.data);
                if (response.data.products.length === 0) {
                    setSearchError({
                        type: 'no_results',
                        message: `No products found for "${query}". Try a different name or use the "Type Ingredients" tab.`
                    });
                }
            } else {
                setShowDropdown(true);
                setSearchError({
                    type: 'error',
                    message: response.data.message || 'Search failed. Please try again.'
                });
            }
        } catch (error) {
            // Ignore aborted requests (user typed new query)
            if (error.name === 'AbortError' || error.name === 'CanceledError') return;
            // Ignore if query changed
            if (searchQueryRef.current !== thisQuery) return;

            console.error('Search error:', error);
            setShowDropdown(true);
            setSearchError({
                type: 'error',
                message: 'Search is taking too long. Please retry.'
            });
        } finally {
            // Only stop spinner if this is still the active query
            if (searchQueryRef.current === thisQuery) {
                setIsSearching(false);
            }
        }
    }, []);

    // Cleanup abort controller on unmount
    useEffect(() => {
        return () => {
            if (abortControllerRef.current) abortControllerRef.current.abort();
            if (searchTimerRef.current) clearTimeout(searchTimerRef.current);
        };
    }, []);

    // Debounced search
    const handleSearchInput = (e) => {
        const value = e.target.value;
        setSearchQuery(value);
        setSelectedProduct(null);

        if (searchTimerRef.current) {
            clearTimeout(searchTimerRef.current);
        }

        if (value.trim().length >= 2) {
            setIsSearching(true);
            setShowDropdown(true);
            setSearchError(null);
            // Don't clear old results — keep showing them while new ones load
            // Only show skeletons if there are truly no results yet
        } else {
            // Cancel any pending request
            if (abortControllerRef.current) abortControllerRef.current.abort();
            setIsSearching(false);
            setShowDropdown(false);
            setSearchResults([]);
            setSearchError(null);
        }

        searchTimerRef.current = setTimeout(() => {
            searchProducts(value);
        }, 150);  // ⚡ Reduced from 300ms — snappier search
    };

    const handleSearchSubmit = (e) => {
        e.preventDefault();
        if (searchTimerRef.current) clearTimeout(searchTimerRef.current);
        searchProducts(searchQuery);
    };

    // Analyze selected product
    const handleAnalyzeProduct = async (product) => {
        setSelectedProduct(product);
        setIsAnalyzingProduct(true);
        setShowDropdown(false);
        setValidationError(null);

        try {
            const response = await api.post('/api/analyze-product/', {
                barcode: product.barcode,
                ingredients_text: product.ingredients_text || ''
            });

            if (response.data.success === false) {
                // Product found but no ingredients or analysis failed
                setValidationError({
                    title: 'Cannot Analyze',
                    message: response.data.message || 'Could not analyze this product.',
                    suggestion: 'Try switching to the "Type Ingredients" tab and entering the ingredients manually.'
                });
                setSelectedProduct(null);
                return;
            }

            if (response.data.is_valid_ingredient_list === false) {
                setValidationError({
                    title: 'Invalid Ingredients',
                    message: response.data.validation_message || 'The ingredient data for this product could not be analyzed.',
                    suggestion: 'Try typing the ingredients manually in the other tab.'
                });
                setSelectedProduct(null);
                return;
            }

            setValidationError(null);
            // Attach product metadata for alternatives & history
            const productInfo = response.data.product_info || {};
            const meta = {
                name: product.name || '',
                brand: product.brand || '',
                image_url: product.image_url || '',
                categories: product.categories || '',
                nutriscore_grade: product.nutriscore_grade || '',
                barcode: product.barcode || '',
                nutriments: productInfo.nutriments || product.nutriments || null,
            };
            response.data._product_meta = meta;

            // ⚡ Prefetch alternatives in background (non-blocking)
            // So they're ready instantly when ResultsSection mounts
            if (meta.categories) {
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
                            setPrefetchedAlternatives(
                                meta.categories, meta.nutriscore_grade, meta.name,
                                res.data.alternatives
                            );
                        }
                    })
                    .catch(() => { }); // Silent — ResultsSection will retry if needed
            }

            onAnalyze(response.data, null);
        } catch (error) {
            console.error('Product analysis error:', error);
            const status = error?.response?.status;
            if (status === 429) {
                setValidationError({
                    title: 'Too Many Requests',
                    message: 'You\'ve made too many analysis requests. Please wait a minute and try again.',
                    suggestion: ''
                });
            } else {
                setValidationError({
                    title: 'Analysis Failed',
                    message: 'Could not analyze this product. Please try again.',
                    suggestion: 'You can also try typing the ingredients manually.'
                });
            }
            setSelectedProduct(null);
        } finally {
            setIsAnalyzingProduct(false);
        }
    };

    // Cleanup timer on unmount
    useEffect(() => {
        return () => {
            if (searchTimerRef.current) clearTimeout(searchTimerRef.current);
        };
    }, []);

    // ========================================
    //  MANUAL TEXT TAB LOGIC
    // ========================================

    const handleAnalysisError = (errorData) => {
        const { error, message, suggestions } = errorData;
        let alertMessage = message || 'An error occurred during analysis.';
        if (suggestions && suggestions.length > 0) {
            alertMessage += '\n\nSuggestions:\n' + suggestions.map((s, i) => `${i + 1}. ${s}`).join('\n');
        }
        setValidationError({
            title: 'Analysis Error',
            message: alertMessage,
            suggestion: 'Please try again or check the suggestions above.'
        });
    };

    const handleManualTextAnalyze = async () => {
        if (!manualText.trim()) {
            setValidationError({
                title: 'Empty Input',
                message: 'Please enter ingredients to analyze.',
                suggestion: 'Type or paste the list of ingredients from the product label.'
            });
            return;
        }

        const text = manualText.toLowerCase();
        const invalidPatterns = [
            /\b(i am|i'm|my name|hello|hi there|test|lorem ipsum)\b/i,
            /\b(student|developer|engineer|work on|interested in|building|handling)\b/i,
            /\b(how are you|what is|please|thank you|can you)\b/i,
            /\b(backend|frontend|full-stack|api|authentication|systems)\b/i,
            /\b(computer science|programming|coding|development)\b/i,
        ];

        const hasInvalidPattern = invalidPatterns.some(pattern => pattern.test(text));
        const wordCount = text.split(/\s+/).length;
        const hasCommonVerbs = /\b(am|is|are|was|were|be|been|have|has|had|do|does|did|will|would|could|should)\b/i.test(text);
        const looksLikeSentence = wordCount > 5 && hasCommonVerbs && !text.includes(',');

        if (hasInvalidPattern || looksLikeSentence) {
            setValidationError({
                title: 'Not a Valid Ingredient List',
                message: 'This doesn\'t look like a food ingredient list.',
                suggestion: 'Please enter actual food ingredients separated by commas or line breaks.',
                example: 'Example: "Flour, Water, Sugar, Eggs, Salt" or "Wheat Flour\nPalm Oil\nSugar\nSalt"'
            });
            return;
        }

        setIsLoading(true);

        try {
            const response = await api.post('/api/analyze/text/', { text: manualText });

            if (response.data.success === false) {
                handleAnalysisError(response.data);
                return;
            }

            if (response.data.is_valid_ingredient_list === false) {
                const validationMsg = response.data.validation_message ||
                    'The text you entered does not appear to be a food ingredient list.';
                setValidationError({
                    title: 'Not a Valid Ingredient List',
                    message: validationMsg,
                    suggestion: 'Please enter actual food ingredients (e.g., "Flour, Sugar, Eggs, Milk") not random text or sentences.'
                });
                return;
            }

            setValidationError(null);
            onAnalyze(response.data, null);
        } catch (error) {
            console.error('Analysis error:', error);
            if (error.response && error.response.data) {
                handleAnalysisError(error.response.data);
            } else {
                setValidationError({
                    title: 'Connection Error',
                    message: 'Failed to connect to the server.',
                    suggestion: 'Please check your internet connection and try again.'
                });
            }
        } finally {
            setIsLoading(false);
        }
    };

    // ========================================
    //  RENDER
    // ========================================

    return (
        <section className="upload-section">
            <div className="upload-container">
                <h1 className="main-title">Discover What's Inside Your Food</h1>
                <p className="main-subtitle">
                    Search a product or enter ingredients to get analysis
                </p>

                {/* Tab Switcher */}
                <div className="upload-tabs" id="upload-tabs">
                    <button
                        className={`tab-btn ${activeTab === 'search' ? 'active' : ''}`}
                        onClick={() => { setActiveTab('search'); setValidationError(null); }}
                        id="tab-search"
                    >
                        <svg className="tab-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                            <circle cx="11" cy="11" r="8" />
                            <path d="M21 21l-4.35-4.35" />
                        </svg>
                        Search Product
                    </button>
                    <button
                        className={`tab-btn ${activeTab === 'manual' ? 'active' : ''}`}
                        onClick={() => { setActiveTab('manual'); setValidationError(null); }}
                        id="tab-manual"
                    >
                        <svg className="tab-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                            <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7" />
                            <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z" />
                        </svg>
                        Type Ingredients
                    </button>
                </div>

                {/* Validation Error Display */}
                {validationError && (
                    <div className="validation-error-card">
                        <div className="error-icon">
                            <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                                <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="2" />
                                <path d="M12 8v4M12 16h.01" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
                            </svg>
                        </div>
                        <div className="error-content">
                            <h3 className="error-title">{validationError.title}</h3>
                            <p className="error-message">{validationError.message}</p>
                            <p className="error-suggestion">{validationError.suggestion}</p>
                            {validationError.example && (
                                <div className="error-example">{validationError.example}</div>
                            )}
                        </div>
                        <button
                            className="error-close-btn"
                            onClick={() => setValidationError(null)}
                            aria-label="Close error"
                        >
                            <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                                <path d="M18 6L6 18M6 6l12 12" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
                            </svg>
                        </button>
                    </div>
                )}

                {/* ===== SEARCH TAB ===== */}
                {activeTab === 'search' && (
                    <div className="upload-box search-active" style={{ animation: 'fadeIn 0.3s ease-out' }}>

                        {/* Analysis Loading Overlay */}
                        {isAnalyzingProduct && selectedProduct ? (
                            <div className="analysis-overlay">
                                <div className="analysis-overlay-content">
                                    <div className="analysis-product-preview">
                                        {selectedProduct.image_url && (
                                            <img src={selectedProduct.image_url} alt="" className="analysis-preview-img" />
                                        )}
                                        <div className="analysis-preview-info">
                                            <span className="analysis-preview-name">{selectedProduct.name}</span>
                                            <span className="analysis-preview-brand">{selectedProduct.brand}</span>
                                        </div>
                                    </div>
                                    <div className="analysis-dots-loader">
                                        <span className="analysis-dot"></span>
                                        <span className="analysis-dot"></span>
                                        <span className="analysis-dot"></span>
                                    </div>
                                    <div className="analysis-loading-message" key={loadingMsgIndex}>
                                        <span className="analysis-msg-icon">{ANALYSIS_MESSAGES[loadingMsgIndex].icon}</span>
                                        <span className="analysis-msg-text">{ANALYSIS_MESSAGES[loadingMsgIndex].text}</span>
                                    </div>
                                </div>
                            </div>
                        ) : (
                            <>
                                {/* Search Input + Dropdown */}
                                <div className="search-dropdown-container" ref={dropdownRef}>
                                    <form onSubmit={handleSearchSubmit} className="product-search-form">
                                        <div className="search-input-wrapper">
                                            <svg className="search-input-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                                                <circle cx="11" cy="11" r="8" />
                                                <path d="M21 21l-4.35-4.35" />
                                            </svg>
                                            <input
                                                ref={searchInputRef}
                                                type="text"
                                                className={`search-input ${showDropdown ? 'dropdown-open' : ''}`}
                                                placeholder="Search for a product... (e.g. Maggi, Parle-G, Amul Butter)"
                                                value={searchQuery}
                                                onChange={handleSearchInput}
                                                onFocus={() => {
                                                    if (searchQuery.trim().length >= 2) {
                                                        setShowDropdown(true);
                                                    }
                                                }}
                                                autoFocus
                                                autoComplete="off"
                                                id="product-search-input"
                                            />

                                            {/* Clear Button */}
                                            {searchQuery && (
                                                <button
                                                    type="button"
                                                    className="search-clear-btn"
                                                    onClick={() => {
                                                        setSearchQuery('');
                                                        setSearchResults([]);
                                                        setShowDropdown(false);
                                                        setSearchError(null);
                                                        document.getElementById('product-search-input').focus();
                                                    }}
                                                    aria-label="Clear search"
                                                    title="Clear search"
                                                >
                                                    ×
                                                </button>
                                            )}

                                            {isSearching && <span className="search-spinner"></span>}
                                        </div>
                                    </form>

                                    {/* Floating Dropdown */}
                                    {showDropdown && (
                                        <div className="search-dropdown">
                                            {/* Skeletons while loading */}
                                            {isSearching && searchResults.length === 0 && (
                                                <>
                                                    <div className="dropdown-header">
                                                        <span className="dropdown-header-text">Searching...</span>
                                                    </div>
                                                    <div className="search-results-list">
                                                        {[1, 2, 3, 4, 5].map((i) => (
                                                            <div key={i} className="skeleton-result-item" style={{ animationDelay: `${i * 0.05}s` }}>
                                                                <div className="skeleton-image skeleton-shimmer"></div>
                                                                <div className="skeleton-info">
                                                                    <div className="skeleton-name skeleton-shimmer"></div>
                                                                    <div className="skeleton-brand skeleton-shimmer"></div>
                                                                </div>
                                                                <div className="skeleton-arrow skeleton-shimmer"></div>
                                                            </div>
                                                        ))}
                                                    </div>
                                                </>
                                            )}

                                            {/* Actual Results */}
                                            {searchResults.length > 0 && (
                                                <>
                                                    <div className="dropdown-header">
                                                        <span className="dropdown-header-text">
                                                            {searchResults.length} product{searchResults.length !== 1 ? 's' : ''} found
                                                        </span>
                                                    </div>
                                                    <div className="search-results-list">
                                                        {searchResults.map((product, idx) => (
                                                            <button
                                                                key={product.barcode || idx}
                                                                className={`search-result-item ${selectedProduct?.barcode === product.barcode ? 'selected' : ''}`}
                                                                onClick={() => handleAnalyzeProduct(product)}
                                                                disabled={isAnalyzingProduct}
                                                                id={`search-result-${idx}`}
                                                            >
                                                                <div className="result-image-wrapper">
                                                                    {product.image_url ? (
                                                                        <img
                                                                            src={product.image_url}
                                                                            alt={product.name}
                                                                            className="result-product-image"
                                                                            loading="lazy"
                                                                            decoding="async"
                                                                            onLoad={(e) => { e.target.style.opacity = '1'; }}
                                                                            style={{ opacity: 0, transition: 'opacity 0.3s ease' }}
                                                                            onError={(e) => { e.target.style.display = 'none'; e.target.nextSibling.style.display = 'flex'; }}
                                                                        />
                                                                    ) : null}
                                                                    <div className="result-image-placeholder" style={product.image_url ? { display: 'none' } : {}}>
                                                                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                                                                            <path d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4" />
                                                                        </svg>
                                                                    </div>
                                                                </div>
                                                                <div className="result-info">
                                                                    <span className="result-name">{product.name}</span>
                                                                    <span className="result-brand">
                                                                        {product.brand}
                                                                        {product.country && (
                                                                            <span className={`country-badge ${product.is_indian ? 'indian' : ''}`}>
                                                                                {product.is_indian ? '🇮🇳' : ''} {product.country}
                                                                            </span>
                                                                        )}
                                                                    </span>
                                                                    {product.categories && (
                                                                        <span className="result-category">{product.categories.split(',')[0]}</span>
                                                                    )}
                                                                </div>
                                                                <div className="result-action">
                                                                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{ width: '20px', height: '20px', color: 'var(--color-accent-primary)' }}>
                                                                        <path d="M5 12h14M12 5l7 7-7 7" />
                                                                    </svg>
                                                                </div>
                                                            </button>
                                                        ))}
                                                    </div>
                                                </>
                                            )}

                                            {/* No Results */}
                                            {searchError && searchError.type === 'no_results' && !isSearching && (
                                                <div className="search-no-results">
                                                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" style={{ width: '40px', height: '40px', color: 'var(--color-text-tertiary)', marginBottom: '8px' }}>
                                                        <circle cx="11" cy="11" r="8" />
                                                        <path d="M21 21l-4.35-4.35" />
                                                        <path d="M8 11h6" />
                                                    </svg>
                                                    <p className="no-results-text">{searchError.message}</p>
                                                    <button
                                                        className="switch-tab-btn"
                                                        onClick={() => setActiveTab('manual')}
                                                    >
                                                        Type Ingredients Instead →
                                                    </button>
                                                </div>
                                            )}

                                            {/* API Error / Timeout */}
                                            {searchError && searchError.type === 'error' && !isSearching && (
                                                <div className="search-no-results">
                                                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" style={{ width: '40px', height: '40px', color: 'var(--color-accent-primary)', marginBottom: '8px' }}>
                                                        <circle cx="12" cy="12" r="10" />
                                                        <path d="M12 8v4M12 16h.01" />
                                                    </svg>
                                                    <p className="no-results-text">{searchError.message}</p>
                                                    <button
                                                        className="switch-tab-btn"
                                                        onClick={() => {
                                                            setSearchError(null);
                                                            setIsSearching(true);
                                                            searchProducts(searchQuery);
                                                        }}
                                                    >
                                                        🔄 Retry Search
                                                    </button>
                                                </div>
                                            )}
                                        </div>
                                    )}
                                </div>

                                {/* Empty state — suggestion chips + scan history */}
                                {!searchQuery && searchResults.length === 0 && !isSearching && (
                                    <div className="search-empty-state">
                                        <div className="search-suggestions">
                                            <p className="suggestions-label">Popular searches:</p>
                                            <div className="suggestion-chips">
                                                {['Maggi', 'Parle-G', 'Amul Butter', 'Haldiram', 'Britannia', 'Kurkure'].map((term) => (
                                                    <button
                                                        key={term}
                                                        className="suggestion-chip"
                                                        onClick={() => {
                                                            setSearchQuery(term);
                                                            setIsSearching(true);
                                                            setShowDropdown(true);
                                                            searchProducts(term);
                                                        }}
                                                    >
                                                        {term}
                                                    </button>
                                                ))}
                                            </div>
                                        </div>

                                        {/* Recent scans from localStorage */}
                                        {(() => {
                                            try {
                                                const history = JSON.parse(localStorage.getItem('ingrexa_scan_history') || '[]');
                                                if (history.length === 0) return null;
                                                return (
                                                    <div className="recent-scans-section">
                                                        <div className="recent-scans-header">
                                                            <p className="suggestions-label" style={{ margin: 0 }}>🕐 Recent scans</p>
                                                            {history.length > 4 && (
                                                                <button onClick={() => setShowHistoryModal(true)} className="view-history-btn">
                                                                    View All
                                                                </button>
                                                            )}
                                                        </div>
                                                        <div className="recent-scans-grid">
                                                            {history.slice(0, 4).map((item, idx) => (
                                                                <button
                                                                    key={idx}
                                                                    className="recent-scan-card"
                                                                    onClick={() => {
                                                                        setSearchQuery(item.name);
                                                                        setIsSearching(true);
                                                                        setShowDropdown(true);
                                                                        searchProducts(item.name);
                                                                    }}
                                                                >
                                                                    <div className="recent-scan-img-wrap">
                                                                        {item.image_url ? (
                                                                            <img src={item.image_url} alt="" className="recent-scan-img" />
                                                                        ) : (
                                                                            <div className="recent-scan-placeholder">📦</div>
                                                                        )}
                                                                        {item.nutriscore_grade && item.nutriscore_grade !== 'unknown' && item.nutriscore_grade !== 'not-applicable' && (
                                                                            <span className={`recent-scan-badge badge-${item.nutriscore_grade.toLowerCase()}`}>
                                                                                {item.nutriscore_grade.toUpperCase()}
                                                                            </span>
                                                                        )}
                                                                    </div>
                                                                    <div className="recent-scan-info">
                                                                        <span className="recent-scan-name">{item.name}</span>
                                                                        {item.brand && <span className="recent-scan-brand">{item.brand}</span>}
                                                                    </div>
                                                                </button>
                                                            ))}
                                                        </div>
                                                    </div>
                                                );
                                            } catch { return null; }
                                        })()}
                                    </div>
                                )}
                            </>
                        )}

                    </div>
                )}

                {/* ===== MANUAL TEXT TAB ===== */}
                {activeTab === 'manual' && (
                    <div className="upload-box manual-active" style={{ animation: 'fadeIn 0.3s ease-out' }}>
                        {isLoading ? (
                            <div className="analysis-overlay">
                                <div className="analysis-overlay-content">
                                    <div className="analysis-dots-loader">
                                        <span className="analysis-dot"></span>
                                        <span className="analysis-dot"></span>
                                        <span className="analysis-dot"></span>
                                    </div>
                                    <div className="analysis-loading-message" key={loadingMsgIndex}>
                                        <span className="analysis-msg-icon">{ANALYSIS_MESSAGES[loadingMsgIndex].icon}</span>
                                        <span className="analysis-msg-text">{ANALYSIS_MESSAGES[loadingMsgIndex].text}</span>
                                    </div>
                                </div>
                            </div>
                        ) : (
                            <>
                                <textarea
                                    className="text-input"
                                    placeholder="Paste ingredients here... (e.g. Wheat Flour, Sugar, Palm Oil, Salt)"
                                    value={manualText}
                                    onChange={(e) => setManualText(e.target.value)}
                                ></textarea>
                                <button
                                    className="analyze-btn"
                                    onClick={handleManualTextAnalyze}
                                    disabled={!manualText.trim()}
                                >
                                    Analyze Ingredients
                                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                        <path d="M5 12h14M12 5l7 7-7 7" />
                                    </svg>
                                </button>
                                <div className="helper-text">
                                    Tip: You can copy and paste the ingredient list directly from any product website.
                                </div>
                            </>
                        )}
                    </div>
                )}
            </div>

            {/* History Modal Overlay */}
            {showHistoryModal && (
                <div className="history-modal-overlay" onClick={() => setShowHistoryModal(false)}>
                    <div className="history-modal-content" onClick={e => e.stopPropagation()}>
                        <div className="history-modal-header">
                            <div>
                                <h1 className="history-title">Your Scan History</h1>
                                <p className="history-subtitle">Find your previously analyzed products</p>
                            </div>
                            <button className="history-modal-close" onClick={() => setShowHistoryModal(false)} aria-label="Close history">
                                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                                    <line x1="18" y1="6" x2="6" y2="18"></line>
                                    <line x1="6" y1="6" x2="18" y2="18"></line>
                                </svg>
                            </button>
                        </div>
                        <div className="history-modal-body">
                            {(() => {
                                const history = JSON.parse(localStorage.getItem('ingrexa_scan_history') || '[]');
                                return history.map((item, idx) => (
                                    <button
                                        key={idx}
                                        className="history-list-item"
                                        onClick={() => {
                                            setShowHistoryModal(false);
                                            setSearchQuery(item.name);
                                            setIsSearching(true);
                                            setShowDropdown(true);
                                            searchProducts(item.name);
                                        }}
                                    >
                                        <div className="history-item-img-wrap">
                                            {item.image_url ? (
                                                <img src={item.image_url} alt="" className="history-item-img" />
                                            ) : (
                                                <div className="history-item-placeholder">📦</div>
                                            )}
                                            {item.nutriscore_grade && item.nutriscore_grade !== 'unknown' && item.nutriscore_grade !== 'not-applicable' && (
                                                <span className={`history-item-badge badge-${item.nutriscore_grade.toLowerCase()}`}>
                                                    {item.nutriscore_grade.toUpperCase()}
                                                </span>
                                            )}
                                        </div>
                                        <div className="history-item-info">
                                            <span className="history-item-name">{item.name}</span>
                                            {item.brand && <span className="history-item-brand">{item.brand}</span>}
                                            {item.scannedAt && (
                                                <span className="history-item-date">
                                                    {new Date(item.scannedAt).toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' })}
                                                </span>
                                            )}
                                        </div>
                                        <div className="history-item-arrow">
                                            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                                                <path d="M5 12h14M12 5l7 7-7 7" />
                                            </svg>
                                        </div>
                                    </button>
                                ));
                            })()}
                        </div>
                    </div>
                </div>
            )
            }
        </section >
    );
}

export { getPrefetchedAlternatives };
export default UploadSection;
