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
    const [currentPage, setCurrentPage] = useState(
        () => sessionStorage.getItem('ingrexa_current_page') || 'home'
    );
    const [showResults, setShowResults] = useState(false);
    const [analysisData, setAnalysisData] = useState(null);
    const [uploadedImage, setUploadedImage] = useState(null);
    const [user, setUser] = useState(null);

    // Dark mode — persists in localStorage
    const [isDark, setIsDark] = useState(() => {
        const saved = localStorage.getItem('ingrexa_theme');
        return saved ? saved === 'dark' : window.matchMedia('(prefers-color-scheme: dark)').matches;
    });

    useEffect(() => {
        document.documentElement.setAttribute('data-theme', isDark ? 'dark' : 'light');
        localStorage.setItem('ingrexa_theme', isDark ? 'dark' : 'light');
    }, [isDark]);

    const toggleDarkMode = () => setIsDark(prev => !prev);

    const logout = useCallback(() => {
        clearAccessToken();
        setUser(null);
        api.post('/api/auth/logout/').catch(() => {});
        sessionStorage.removeItem('ingrexa_current_page');
    }, []);

    const fetchUser = useCallback(async () => {
        if (!getAccessToken()) return;
        try {
            const res = await api.get('/api/auth/me/');
            if (res.data?.success) setUser(res.data.user);
        } catch (err) {
            if (err.response?.status === 401 || err.response?.status === 403) logout();
        }
    }, [logout]);

    useEffect(() => {
        const onExpired = () => {
            setUser(null);
            setCurrentPage('login');
        };
        window.addEventListener('ingrexa:session-expired', onExpired);
        return () => window.removeEventListener('ingrexa:session-expired', onExpired);
    }, []);

    useGoogleOneTapLogin({
        onSuccess: async (credentialResponse) => {
            try {
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
                console.error('One Tap login failed', err);
            }
        },
        onError: () => console.error('One Tap login failed'),
        disabled: !!user || !!getAccessToken(),
    });

    useEffect(() => {
        const restoreSession = async () => {
            try {
                const res = await api.post('/api/auth/token/refresh/', {}, { withCredentials: true });
                if (res.data?.access) {
                    setAccessToken(res.data.access);
                    await fetchUser();
                }
            } catch {
                // no refresh cookie, user stays logged out
            }
        };
        restoreSession();
    }, [fetchUser]);

    useEffect(() => {
        window.scrollTo(0, 0);
        const t = setTimeout(() => window.scrollTo(0, 0), 10);
        return () => clearTimeout(t);
    }, [currentPage, showResults]);

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
        if (currentPage === 'home') return <HomePage onNavigate={handleNavigate} user={user} />;
        if (currentPage === 'contact') return <ContactPage />;

        if (currentPage === 'login' || currentPage === 'signup') {
            if (user) {
                setTimeout(() => handleNavigate('analyze'), 0);
                return <UploadSection onAnalyze={handleAnalyze} user={user} />;
            }
            const onLoginSuccess = (token) => { setAccessToken(token); fetchUser(); };
            if (currentPage === 'login') return <LoginPage onNavigate={handleNavigate} onLoginSuccess={onLoginSuccess} />;
            return <SignupPage onNavigate={handleNavigate} onLoginSuccess={onLoginSuccess} />;
        }

        if (currentPage === 'settings') return <SettingsPage onNavigate={handleNavigate} user={user} setUser={setUser} />;
        if (currentPage === 'history') return <HistoryPage onNavigate={handleNavigate} user={user} onSelectHistoryItem={handleHistorySelect} />;

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
            <Header onNavigate={handleNavigate} currentPage={currentPage} user={user} setUser={setUser} isDark={isDark} toggleDarkMode={toggleDarkMode} />
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
