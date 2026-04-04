import React, { useState, useEffect } from 'react';
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
import api from './api';

import { useGoogleOneTapLogin } from '@react-oauth/google';

function App() {
    // Current state management...
    const [currentPage, setCurrentPage] = useState(() => {
        return sessionStorage.getItem('ingrexa_current_page') || 'home';
    });
    const [showResults, setShowResults] = useState(false);
    const [analysisData, setAnalysisData] = useState(null);
    const [uploadedImage, setUploadedImage] = useState(null);
    const [user, setUser] = useState(() => {
        const cached = localStorage.getItem('ingrexa_cached_user');
        return cached ? JSON.parse(cached) : null;
    });

    const fetchUser = async () => {
        const token = localStorage.getItem('access_token');
        if (token) {
            try {
                const res = await api.get('/api/auth/me/');
                if (res.data && res.data.success) {
                    const userData = res.data.user;
                    setUser(userData);
                    localStorage.setItem('ingrexa_cached_user', JSON.stringify(userData));
                }
            } catch (err) {
                console.error("Auth verify error", err);
                if (err.response && (err.response.status === 401 || err.response.status === 403)) {
                    localStorage.clear();
                    setUser(null);
                }
            }
        }
    };

    // Google One Tap Implementation
    useGoogleOneTapLogin({
        onSuccess: async (credentialResponse) => {
            try {
                const response = await api.post('/api/auth/google-login/', {
                    credential: credentialResponse.credential
                });
                
                if (response.data.success) {
                    localStorage.setItem('access_token', response.data.access);
                    localStorage.setItem('refresh_token', response.data.refresh);
                    await fetchUser();
                    // Optional: redirect to analyzer if they were on a restricted page
                }
            } catch (err) {
                console.error('One Tap Login error', err);
            }
        },
        onError: () => console.log('One Tap Login Failed'),
        disabled: !!user || !!localStorage.getItem('access_token'),
    });

    // Global auth listener — run once on mount
    useEffect(() => {
        fetchUser();
    }, []);

    // Scroll to top when page or view changes
    useEffect(() => {
        // Force scroll to top on every view/page change
        window.scrollTo(0, 0);
        // Secondary safety for mobile/delayed renders
        const timer = setTimeout(() => window.scrollTo(0, 0), 10);
        return () => clearTimeout(timer);
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
        // Synthesize metadata for ResultsSection so it doesn't show "manual ingredients" message
        const analysisWithMeta = {
            ...item.analysis_json,
            _product_meta: {
                name: item.name || item.product_name,
                brand: item.brand || item.product_brand,
                image_url: item.image_url,
                nutriscore_grade: item.grade || item.nutriscore_grade,
                nutriments: item.analysis_json?.product_info?.nutriments || null
            }
        };
        setAnalysisData(analysisWithMeta);
        setUploadedImage(item.image_url || null);
        setShowResults(true);
        setCurrentPage('analyze');
        sessionStorage.setItem('ingrexa_current_page', 'analyze');
    };

    const renderContent = () => {
        const isLoggedIn = !!user || !!localStorage.getItem('access_token');

        if (currentPage === 'home') return <HomePage onNavigate={handleNavigate} />;
        if (currentPage === 'contact') return <ContactPage />;

        // If already logged in, don't show auth pages — redirect to analyze
        if (currentPage === 'login' || currentPage === 'signup') {
            if (isLoggedIn) {
                // Silently fix the stuck page state
                setTimeout(() => handleNavigate('analyze'), 0);
                return <UploadSection onAnalyze={handleAnalyze} user={user} />;
            }
            if (currentPage === 'login') return <LoginPage onNavigate={handleNavigate} onLoginSuccess={fetchUser} />;
            if (currentPage === 'signup') return <SignupPage onNavigate={handleNavigate} onLoginSuccess={fetchUser} />;
        }

        if (currentPage === 'settings') return <SettingsPage onNavigate={handleNavigate} user={user} setUser={setUser} />;
        if (currentPage === 'history') return <HistoryPage onNavigate={handleNavigate} user={user} onSelectHistoryItem={handleHistorySelect} />;
        
        // Enforce Login Wall for Analyzer
        const token = localStorage.getItem('access_token');
        if (!token) {
            return <LoginPage onNavigate={handleNavigate} onLoginSuccess={fetchUser} />;
        }

        return (!showResults || !analysisData) ? (
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
                <main className="main-content">
                    {renderContent()}
                </main>
            )}
            <Footer />
        </>
    );
}

export default App;
