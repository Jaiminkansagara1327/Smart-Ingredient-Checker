import React, { useState } from 'react';
import api from '../api';

function UploadSection({ onAnalyze }) {
    const [manualText, setManualText] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [validationError, setValidationError] = useState(null);

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

        // Quick frontend validation - reject obvious non-ingredient patterns
        const text = manualText.toLowerCase();
        const invalidPatterns = [
            /\b(i am|i'm|my name|hello|hi there|test|lorem ipsum)\b/i,
            /\b(student|developer|engineer|work on|interested in|building|handling)\b/i,
            /\b(how are you|what is|please|thank you|can you)\b/i,
            /\b(backend|frontend|full-stack|api|authentication|systems)\b/i,
            /\b(computer science|programming|coding|development)\b/i,
        ];

        const hasInvalidPattern = invalidPatterns.some(pattern => pattern.test(text));

        // Check if it looks like sentences (multiple words with common sentence structure)
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

            // Check if analysis was successful
            if (response.data.success === false) {
                handleAnalysisError(response.data);
                return;
            }

            // Check if the AI detected that this is not a valid ingredient list
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

            // Clear any previous errors
            setValidationError(null);

            onAnalyze(response.data, null);
        } catch (error) {
            console.error('Analysis error:', error);

            // Check if it's an API error response
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

    return (
        <section className="upload-section">
            <div className="upload-container">
                <h1 className="main-title">Discover What's Inside Your Food</h1>
                <p className="main-subtitle">
                    Enter ingredients below to get instant analysis
                </p>

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

                <div className="upload-box manual-active">
                    <textarea
                        className="text-input"
                        placeholder="Paste ingredients here... (e.g. Wheat Flour, Sugar, Palm Oil, Salt)"
                        value={manualText}
                        onChange={(e) => setManualText(e.target.value)}
                    ></textarea>
                    <button
                        className="analyze-btn"
                        onClick={handleManualTextAnalyze}
                        disabled={isLoading || !manualText.trim()}
                    >
                        {isLoading ? (
                            <>
                                <span className="spinner"></span>
                                Analyzing...
                            </>
                        ) : (
                            <>
                                Analyze Ingredients
                                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                    <path d="M5 12h14M12 5l7 7-7 7" />
                                </svg>
                            </>
                        )}
                    </button>
                    <div className="helper-text">
                        Tip: You can copy and paste the ingredient list directly from any product website.
                    </div>
                </div>
            </div>
        </section>
    );
}

export default UploadSection;
