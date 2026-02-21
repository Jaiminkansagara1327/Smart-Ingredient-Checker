import React, { useState } from 'react';
import Header from './components/Header';
import HomePage from './components/HomePage';
import UploadSection from './components/UploadSection';
import ResultsSection from './components/ResultsSection';
import ContactPage from './components/ContactPage';
import Footer from './components/Footer';

function App() {
    const [currentPage, setCurrentPage] = useState('home');
    const [showResults, setShowResults] = useState(false);
    const [analysisData, setAnalysisData] = useState(null);
    const [uploadedImage, setUploadedImage] = useState(null);

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
        setCurrentPage(page);
        setShowResults(false);
    };

    const renderContent = () => {
        if (currentPage === 'home') return <HomePage onNavigate={handleNavigate} />;
        if (currentPage === 'contact') return <ContactPage />;

        return !showResults ? (
            <UploadSection onAnalyze={handleAnalyze} />
        ) : (
            <ResultsSection
                data={analysisData}
                image={uploadedImage}
                onAnalyzeNew={handleAnalyzeNew}
            />
        );
    };

    return (
        <>
            <Header onNavigate={handleNavigate} currentPage={currentPage} />
            <main className="main-content">
                {renderContent()}
            </main>
            <Footer />
        </>
    );
}

export default App;
