import React, { useState, useEffect, useCallback } from 'react';
import Header from './components/Layout/Header';
import HomePage from './components/Home/HomePage';
import UploadSection from './components/Analyzer/UploadSection';
import ResultsSection from './components/Analyzer/ResultsSection';
import ContactPage from './components/Other/ContactPage';
import LoginPage from './components/Auth/LoginPage';
import SignupPage from './components/Auth/SignupPage';
import SettingsPage from './components/Other/SettingsPage';
import HistoryPage from './components/Other/HistoryPage';
import Footer from './components/Layout/Footer';

import api, { setAccessToken, clearAccessToken, getAccessToken } from './api';

import { useGoogleOneTapLogin } from '@react-oauth/google';
import { generateNonce } from './utils/nonce';

function App() {
    const [currentPage, setCurrentPage] = useState(() =>
        sessionStorage.getItem('ingrexa_current_page') || 'home'
    );
    const [showResults, setShowResults] = useState(false);
    const [analysisData, setAnalysisData] = useState(null);
    const [uploadedImage, setUploadedImage] = useState(null);

    // User state: populated from /api/auth/me/ — NOT from localStorage
    const [user, setUser] = useState(null);

    // ── Auth helpers ──────────────────────────────────────────────────────────

    const logout = useCallback(() => {
        clearAccessToken();
        setUser(null);
        // Tell the backend to blacklist the refresh cookie
        api.post('/api/auth/logout/').catch(() => {});
        sessionStorage.removeItem('ingrexa_current_page');
    }, []);

    const fetchUser = useCallback(async () => {
        if (!getAccessToken()) return;
        try {
            const res = await api.get('/api/auth/me/');
            if (res.data?.success) {
                setUser(res.data.user);
            }
        } catch (err) {
            if (err.response?.status === 401 || err.response?.status === 403) {
                logout();
            }
        }
    }, [logout]);

    // ── Session expired event (fired by api.js interceptor) ───────────────────
    useEffect(() => {
        const onExpired = () => {
            setUser(null);
            setCurrentPage('login');
        };
        window.addEventListener('ingrexa:session-expired', onExpired);
        return () => window.removeEventListener('ingrexa:session-expired', onExpired);
    }, []);

    // ── Google One Tap ────────────────────────────────────────────────────────
    useGoogleOneTapLogin({
        onSuccess: async (credentialResponse) => {
            try {
                // Generate + send a nonce so the backend can validate it (finding #8)
                const nonce = generateNonce();
                const response = await api.post('/api/auth/google-login/', {
                    credential: credentialResponse.credential,
                    nonce,
                });
                if (response.data.success) {
                    setAccessToken(response.data.access);
                    await fetchUser();
                }
            } catch (err) {
                console.error('One Tap Login error', err);
            }
        },
        onError: () => console.log('One Tap Login Failed'),
        disabled: !!user || !!getAccessToken(),
    });

    // ── On mount: try to restore session via refresh cookie ──────────────────
    useEffect(() => {
        const restoreSession = async () => {
            try {
                const res = await api.post('/api/auth/token/refresh/', {}, { withCredentials: true });
                if (res.data?.access) {
                    setAccessToken(res.data.access);
                    await fetchUser();
                }
            } catch {
                // No valid refresh cookie; user is logged out — that's fine
            }
        };
        restoreSession();
    }, [fetchUser]);

    // ── Scroll reset ──────────────────────────────────────────────────────────
    useEffect(() => {
        window.scrollTo(0, 0);
        const timer = setTimeout(() => window.scrollTo(0, 0), 10);
        return () => clearTimeout(timer);
    }, [currentPage, showResults]);

    // ── Event handlers ────────────────────────────────────────────────────────

    const handleAnalyze = (data, image) => {
        setAnalysisData(data);
        setUploadedImage(image);
        setShowResults(true);
    };

    const handleAnalyzeNew = () => {
        setShowResults(false);
        setAnalysisData(null);
        setUploadedImage(null);
    };

    const handleNavigate = (page) => {
        if (typeof page === 'object' && page.type === 'history_item') {
            handleHistorySelect(page.item);
            return;
        }
        setCurrentPage(page);
        sessionStorage.setItem('ingrexa_current_page', page);
        setShowResults(false);
    };

    const handleHistorySelect = (item) => {
        const analysisWithMeta = {
            ...item.analysis_json,
            _product_meta: {
                name: item.name || item.product_name,
                brand: item.brand || item.product_brand,
                image_url: item.image_url,
                nutriscore_grade: item.grade || item.nutriscore_grade,
                nutriments: item.analysis_json?.product_info?.nutriments || null,
            },
        };
        setAnalysisData(analysisWithMeta);
        setUploadedImage(item.image_url || null);
        setShowResults(true);
        setCurrentPage('analyze');
        sessionStorage.setItem('ingrexa_current_page', 'analyze');
    };

    const renderContent = () => {
        const isLoggedIn = !!user;

        if (currentPage === 'home') return <HomePage onNavigate={handleNavigate} user={user} />;
        if (currentPage === 'contact') return <ContactPage />;

        if (currentPage === 'login' || currentPage === 'signup') {
            if (isLoggedIn) {
                setTimeout(() => handleNavigate('analyze'), 0);
                return <UploadSection onAnalyze={handleAnalyze} user={user} />;
            }
            if (currentPage === 'login')
                return (
                    <LoginPage
                        onNavigate={handleNavigate}
                        onLoginSuccess={(accessToken) => {
                            setAccessToken(accessToken);
                            fetchUser();
                        }}
                    />
                );
            if (currentPage === 'signup')
                return (
                    <SignupPage
                        onNavigate={handleNavigate}
                        onLoginSuccess={(accessToken) => {
                            setAccessToken(accessToken);
                            fetchUser();
                        }}
                    />
                );
        }

        if (currentPage === 'settings')
            return <SettingsPage onNavigate={handleNavigate} user={user} setUser={setUser} />;
        if (currentPage === 'history')
            return (
                <HistoryPage
                    onNavigate={handleNavigate}
                    user={user}
                    onSelectHistoryItem={handleHistorySelect}
                />
            );

        // Enforce Login Wall for Analyzer — check in-memory token, not localStorage
        if (!getAccessToken()) {
            return <LoginPage onNavigate={handleNavigate} onLoginSuccess={(tok) => { setAccessToken(tok); fetchUser(); }} />;
        }

        return !showResults || !analysisData ? (
            <UploadSection onAnalyze={handleAnalyze} user={user} />
        ) : (
            <ResultsSection
                data={analysisData}
                image={uploadedImage}
                onAnalyzeNew={handleAnalyzeNew}
                onNavigate={handleNavigate}
            />
        );
    };

    return (
        <>
            <Header onNavigate={handleNavigate} currentPage={currentPage} user={user} setUser={setUser} />
            {currentPage === 'home' ? (
                renderContent()
            ) : (
                <main className="main-content">{renderContent()}</main>
            )}
            <Footer />
        </>
    );
}

export default App;
