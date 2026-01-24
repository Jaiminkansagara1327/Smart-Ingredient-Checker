import React, { useState } from 'react';
import Header from './components/Header';
import UploadSection from './components/UploadSection';
import ResultsSection from './components/ResultsSection';

function App() {
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

    return (
        <>
            <Header />
            <main className="main-content">
                {!showResults ? (
                    <UploadSection onAnalyze={handleAnalyze} />
                ) : (
                    <ResultsSection
                        data={analysisData}
                        image={uploadedImage}
                        onAnalyzeNew={handleAnalyzeNew}
                    />
                )}
            </main>
        </>
    );
}

export default App;
