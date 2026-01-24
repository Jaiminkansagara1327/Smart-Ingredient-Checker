import React, { useState } from 'react';
import Header from './components/Header';
import UploadSection from './components/UploadSection';
import ResultsSection from './components/ResultsSection';
import AboutPage from './components/AboutPage';
import Footer from './components/Footer';

function App() {
    const [currentPage, setCurrentPage] = useState('analyze');
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

    return (
        <>
            <Header onNavigate={handleNavigate} currentPage={currentPage} />
            <main className="main-content">
                {currentPage === 'about' ? (
                    <AboutPage />
                ) : (
                    <>
                        {!showResults ? (
                            <UploadSection onAnalyze={handleAnalyze} />
                        ) : (
                            <ResultsSection
                                data={analysisData}
                                image={uploadedImage}
                                onAnalyzeNew={handleAnalyzeNew}
                            />
                        )}
                    </>
                )}
            </main>
            <Footer />
        </>
    );
}

export default App;
