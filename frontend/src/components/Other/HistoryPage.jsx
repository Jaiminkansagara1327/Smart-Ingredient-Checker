import React, { useState, useEffect } from 'react';
import api from '../../api';
import '../Auth/AuthPremium.css'; // Utilizing the existing Clinical Sanctuary styles

function HistoryPage({ onNavigate, user, onSelectHistoryItem }) {
    const [history, setHistory] = useState([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchHistoryData = async () => {
            try {
                const histRes = await api.get('/api/history/');
                if (histRes.data && histRes.data.success && histRes.data.items) {
                     const mapped = histRes.data.items.map(item => {
                        let finalName = item.product_name;
                        
                        // If the primary name is generic or missing, check nested JSON data
                        if (!finalName || finalName.trim() === 'Analyzed Product' || finalName.trim() === 'Unknown') {
                            finalName = item.analysis_json?._product_meta?.name || 
                                        item.analysis_json?.product_info?.name || 
                                        item.analysis_json?.product?.name;
                        }

                        // Last resort fallback
                        if (!finalName || finalName.trim() === 'Analyzed Product' || finalName.trim() === 'Unknown') {
                            if (item.input_text_preview) {
                                let snippet = item.input_text_preview.length > 50 
                                    ? item.input_text_preview.substring(0, 47) + '...' 
                                    : item.input_text_preview;
                                finalName = item.input_method === 'text' ? snippet : `Missing Name (Ingredients: ${snippet})`;
                            } else {
                                finalName = item.input_method === 'text' ? 'Custom Label' : 'Unknown Scan';
                            }
                        }

                        return {
                            name: finalName,
                            score: (item.score !== null && item.score !== undefined) ? Number(item.score).toFixed(1) : (item.nutriscore_grade ? item.nutriscore_grade.toUpperCase() : 'N/A'),
                            grade: item.nutriscore_grade || 'unknown',
                            image_url: item.analysis_json?.product?.image_url || item.analysis_json?.product_info?.image_url || item.analysis_json?.image_url || '',
                            date: new Date(item.created_at).toLocaleDateString('en-US', {
                                year: 'numeric',
                                month: 'long',
                                day: 'numeric',
                                hour: '2-digit',
                                minute: '2-digit'
                            }),
                            analysis_json: item.analysis_json
                        };
                    });
                    setHistory(mapped);
                }
            } catch (err) {
                console.error("Failed to load history data", err);
            } finally {
                setLoading(false);
            }
        };

        fetchHistoryData();
    }, []);

    const gradeColorMap = {
        a: '#00A389', // Sprout Green
        b: '#85C441',
        c: '#FECB02',
        d: '#EE8100',
        e: '#E63E11',
        unknown: '#666'
    };

    return (
        <div className="history-page-premium">
            <div className="history-header">
                <div className="history-title-group">
                    <h2 className="history-main-title">Intelligence Log</h2>
                    <p className="history-subtitle">A chronological record of clinical ingredient scans.</p>
                </div>
                <div className="history-icon-pill">
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="10"></circle><polyline points="12 6 12 12 16 14"></polyline></svg>
                </div>
            </div>

            {loading ? (
                <div className="history-loading">
                    <div className="spinner-minimal"></div>
                    <p>Retrieving Log...</p>
                </div>
            ) : history.length === 0 ? (
                <div className="history-empty-state">
                    <div className="empty-icon">📂</div>
                    <h3>Empty Repository</h3>
                    <p>Your analysis history is currently empty. Start by scanning a product label.</p>
                    <button className="btn-ultra-primary" onClick={() => onNavigate('analyze')}>
                        Begin Analysis
                    </button>
                </div>
            ) : (
                <div className="history-list">
                    {history.map((item, idx) => (
                        <div key={idx} 
                            className="history-item-card"
                            onClick={() => onSelectHistoryItem && onSelectHistoryItem(item)}
                        >
                            <div className="history-item-image">
                                {item.image_url ? (
                                    <img src={item.image_url} alt="" loading="lazy" />
                                ) : (
                                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><rect x="2" y="3" width="20" height="14" rx="2" ry="2"></rect><line x1="8" y1="21" x2="16" y2="21"></line><line x1="12" y1="17" x2="12" y2="21"></line></svg>
                                )}
                            </div>
                            <div className="history-item-details">
                                <h4 className="item-name">{item.name}</h4>
                                <div className="item-meta">
                                    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect><line x1="16" y1="2" x2="16" y2="6"></line><line x1="8" y1="2" x2="8" y2="6"></line><line x1="3" y1="10" x2="21" y2="10"></line></svg>
                                    {item.date}
                                </div>
                            </div>
                            <div className="history-item-score">
                                <span className="score-mini-pill" style={{ background: gradeColorMap[item.grade.toLowerCase()] || gradeColorMap.unknown }}>
                                    {item.score !== 'unknown' ? item.score : item.grade.toUpperCase()}
                                </span>
                            </div>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
}

export default HistoryPage;
