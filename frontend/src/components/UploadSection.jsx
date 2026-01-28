import React, { useState, useRef } from 'react';
import axios from 'axios';

function UploadSection({ onAnalyze }) {
    const [activeTab, setActiveTab] = useState('image');
    const [url, setUrl] = useState('');
    const [manualText, setManualText] = useState('');
    const [isDragging, setIsDragging] = useState(false);
    const [isLoading, setIsLoading] = useState(false);
    const fileInputRef = useRef(null);

    const handleFileSelect = async (file) => {
        if (!file) return;

        // Validate file type
        const validTypes = ['image/jpeg', 'image/png', 'image/webp'];
        if (!validTypes.includes(file.type)) {
            alert('Please upload a valid image file (JPG, PNG, or WEBP)');
            return;
        }

        // Validate file size (10MB max)
        const maxSize = 10 * 1024 * 1024;
        if (file.size > maxSize) {
            alert('File size must be less than 10MB');
            return;
        }

        setIsLoading(true);

        try {
            // Create FormData for file upload
            const formData = new FormData();
            formData.append('image', file);

            // Call backend API
            const response = await axios.post('/api/analyze/image/', formData, {
                headers: {
                    'Content-Type': 'multipart/form-data',
                },
            });

            // Check if analysis was successful
            if (response.data.success === false) {
                // Handle error cases
                handleAnalysisError(response.data);
                return;
            }

            // Create image URL for display
            const imageUrl = URL.createObjectURL(file);

            // Pass data to parent
            onAnalyze(response.data, imageUrl);
        } catch (error) {
            console.error('Analysis error:', error);

            // Check if it's an API error response
            if (error.response && error.response.data) {
                handleAnalysisError(error.response.data);
            } else {
                // Network or other error
                alert('Failed to connect to the server. Please check your connection and try again.');
            }
        } finally {
            setIsLoading(false);
        }
    };

    const handleAnalysisError = (errorData) => {
        const { error, message, suggestions } = errorData;

        let alertMessage = message || 'An error occurred during analysis.';

        if (suggestions && suggestions.length > 0) {
            alertMessage += '\n\nSuggestions:\n' + suggestions.map((s, i) => `${i + 1}. ${s}`).join('\n');
        }

        if (error === 'NO_INGREDIENTS_DETECTED') {
            alertMessage += '\n\nPlease make sure you are photographing the ingredient list on the product label.';
        } else if (error === 'LOW_CONFIDENCE') {
            alertMessage += '\n\nTry taking a clearer photo with better lighting.';
        }

        alert(alertMessage);
    };

    const handleUrlAnalyze = async () => {
        if (!url.trim()) {
            alert('Please enter a valid URL');
            return;
        }

        try {
            new URL(url);
        } catch (e) {
            alert('Please enter a valid URL');
            return;
        }

        setIsLoading(true);

        try {
            const response = await axios.post('/api/analyze/url/', { url });

            // Check if analysis was successful
            if (response.data.success === false) {
                handleAnalysisError(response.data);
                return;
            }

            onAnalyze(response.data, null);
        } catch (error) {
            console.error('Analysis error:', error);

            // Check if it's an API error response
            if (error.response && error.response.data) {
                handleAnalysisError(error.response.data);
            } else {
                alert('Failed to connect to the server. Please check your connection and try again.');
            }
        } finally {
            setIsLoading(false);
        }
    };

    const handleManualTextAnalyze = async () => {
        if (!manualText.trim()) {
            alert('Please enter ingredients to analyze');
            return;
        }

        setIsLoading(true);

        try {
            const response = await axios.post('/api/analyze/text/', { text: manualText });

            // Check if analysis was successful
            if (response.data.success === false) {
                handleAnalysisError(response.data);
                return;
            }

            onAnalyze(response.data, null);
        } catch (error) {
            console.error('Analysis error:', error);

            // Check if it's an API error response
            if (error.response && error.response.data) {
                handleAnalysisError(error.response.data);
            } else {
                alert('Failed to connect to the server. Please check your connection and try again.');
            }
        } finally {
            setIsLoading(false);
        }
    };

    const handleDragOver = (e) => {
        e.preventDefault();
        setIsDragging(true);
    };

    const handleDragLeave = () => {
        setIsDragging(false);
    };

    const handleDrop = (e) => {
        e.preventDefault();
        setIsDragging(false);
        const file = e.dataTransfer.files[0];
        handleFileSelect(file);
    };

    const handleClick = () => {
        fileInputRef.current?.click();
    };

    const handleFileInputChange = (e) => {
        const file = e.target.files[0];
        handleFileSelect(file);
    };

    return (
        <section className="upload-section">
            <div className="upload-container">
                <h1 className="main-title">Discover What's Inside Your Food</h1>
                <p className="main-subtitle">
                    Upload an image, paste a URL, or type ingredients to get instant analysis
                </p>

                <div className="upload-tabs">
                    <button
                        className={`tab-btn ${activeTab === 'image' ? 'active' : ''}`}
                        onClick={() => setActiveTab('image')}
                    >
                        <svg className="tab-icon" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                            <rect x="3" y="3" width="18" height="18" rx="2" stroke="currentColor" strokeWidth="2" />
                            <circle cx="8.5" cy="8.5" r="1.5" fill="currentColor" />
                            <path d="M21 15L16 10L5 21" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                        </svg>
                        Upload Image
                    </button>
                    <button
                        className={`tab-btn ${activeTab === 'url' ? 'active' : ''}`}
                        onClick={() => setActiveTab('url')}
                    >
                        <svg className="tab-icon" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                            <path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                            <path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                        </svg>
                        Paste URL
                    </button>
                    <button
                        className={`tab-btn ${activeTab === 'text' ? 'active' : ''}`}
                        onClick={() => setActiveTab('text')}
                    >
                        <svg className="tab-icon" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                            <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                            <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                        </svg>
                        Type Ingredients
                    </button>
                </div>

                <div className="upload-content">
                    {activeTab === 'image' ? (
                        <div className={`tab-content active`}>
                            <div
                                className={`upload-area ${isDragging ? 'dragover' : ''} ${isLoading ? 'loading' : ''}`}
                                onDragOver={handleDragOver}
                                onDragLeave={handleDragLeave}
                                onDrop={handleDrop}
                                onClick={handleClick}
                            >
                                <input
                                    ref={fileInputRef}
                                    type="file"
                                    accept="image/*"
                                    onChange={handleFileInputChange}
                                    style={{ display: 'none' }}
                                />
                                {isLoading ? (
                                    <div className="spinner"></div>
                                ) : (
                                    <>
                                        <svg className="upload-icon" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                                            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                                            <polyline points="17 8 12 3 7 8" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                                            <line x1="12" y1="3" x2="12" y2="15" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                                        </svg>
                                        <h3 className="upload-title">Drop your image here</h3>
                                        <p className="upload-text">or click to browse</p>
                                        <p className="upload-hint">Supports: JPG, PNG, WEBP (Max 10MB)</p>
                                    </>
                                )}
                            </div>
                        </div>
                    ) : activeTab === 'url' ? (
                        <div className={`tab-content active`}>
                            <div className="url-input-container">
                                <input
                                    type="url"
                                    className="url-input"
                                    placeholder="https://example.com/product-page"
                                    value={url}
                                    onChange={(e) => setUrl(e.target.value)}
                                    onKeyPress={(e) => e.key === 'Enter' && handleUrlAnalyze()}
                                    disabled={isLoading}
                                />
                                <button
                                    className="analyze-btn"
                                    onClick={handleUrlAnalyze}
                                    disabled={isLoading}
                                >
                                    {isLoading ? (
                                        <>
                                            <div className="spinner" style={{ width: '20px', height: '20px', margin: 0 }}></div>
                                            <span>Analyzing...</span>
                                        </>
                                    ) : (
                                        <>
                                            <span>Analyze</span>
                                            <svg className="btn-icon" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                                                <line x1="5" y1="12" x2="19" y2="12" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
                                                <polyline points="12 5 19 12 12 19" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                                            </svg>
                                        </>
                                    )}
                                </button>
                            </div>
                        </div>
                    ) : (
                        <div className={`tab-content active`}>
                            <div className="text-input-container">
                                <textarea
                                    className="text-input"
                                    placeholder="Enter ingredients here, separated by commas or line breaks...&#10;&#10;Example:&#10;Water, Sugar, Wheat Flour, Palm Oil, Salt, Milk Powder, Artificial Flavoring"
                                    value={manualText}
                                    onChange={(e) => setManualText(e.target.value)}
                                    disabled={isLoading}
                                    rows={10}
                                />
                                <button
                                    className="analyze-btn"
                                    onClick={handleManualTextAnalyze}
                                    disabled={isLoading}
                                >
                                    {isLoading ? (
                                        <>
                                            <div className="spinner" style={{ width: '20px', height: '20px', margin: 0 }}></div>
                                            <span>Analyzing...</span>
                                        </>
                                    ) : (
                                        <>
                                            <span>Analyze</span>
                                            <svg className="btn-icon" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                                                <line x1="5" y1="12" x2="19" y2="12" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
                                                <polyline points="12 5 19 12 12 19" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                                            </svg>
                                        </>
                                    )}
                                </button>
                            </div>
                        </div>
                    )}
                </div>
            </div>
        </section>
    );
}

export default UploadSection;
