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
        <div className="auth-container" style={{ padding: '2rem 1rem', maxWidth: '800px', margin: '0 auto' }}>
            <div className="auth-card" style={{ padding: '2.5rem', marginTop: '2rem', animation: 'slideUpFade 0.4s ease-out' }}>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '2rem' }}>
                    <div>
                        <h2 style={{ fontSize: '2rem', margin: '0 0 0.5rem 0', fontWeight: '800', color: 'var(--color-text-primary)' }}>
                            Analysis History
                        </h2>
                        <p style={{ margin: '0', color: 'var(--color-text-secondary)', fontSize: '1rem' }}>
                            A complete log of all your ingredient and product scans.
                        </p>
                    </div>
                    <div style={{
                        width: '48px',
                        height: '48px',
                        borderRadius: '12px',
                        backgroundColor: '#f0fdfa',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        color: '#00A389'
                    }}>
                        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="10"></circle><polyline points="12 6 12 12 16 14"></polyline></svg>
                    </div>
                </div>

                <div className="section-divider" style={{ borderBottom: '1px solid #e2e7ff', margin: '2rem 0' }}></div>

                {loading ? (
                    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', padding: '3rem 0', color: '#64748b' }}>
                        <div className="spinner" style={{ borderColor: 'rgba(13, 148, 136, 0.2)', borderTopColor: '#00A389', width: '40px', height: '40px', borderWidth: '4px', marginBottom: '1rem' }}></div>
                        <p style={{ fontWeight: '500' }}>Retrieving your history...</p>
                    </div>
                ) : history.length === 0 ? (
                    <div style={{ backgroundColor: '#f2f3ff', borderRadius: '1.5rem', padding: '3rem 2rem', textAlign: 'center', border: '1px dashed #cbd5e1' }}>
                        <div style={{ fontSize: '3rem', marginBottom: '1rem', opacity: '0.5' }}>🔍</div>
                        <h3 style={{ margin: '0 0 0.5rem 0', fontSize: '1.25rem', color: 'var(--color-text-primary)' }}>No scans found</h3>
                        <p style={{ color: '#64748b', margin: '0 0 2rem 0', maxWidth: '400px', marginLeft: 'auto', marginRight: 'auto' }}>
                            You haven't analyzed any products yet. Scan an ingredient list or product barcode to begin building your history.
                        </p>
                        <button className="auth-btn-primary" onClick={() => onNavigate('analyze')} style={{ width: 'auto', padding: '1rem 2rem', borderRadius: '100px' }}>
                            Start Analyzing
                        </button>
                    </div>
                ) : (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
                        {history.map((item, idx) => (
                            <div key={idx} 
                                onClick={() => onSelectHistoryItem && onSelectHistoryItem(item)}
                                style={{ 
                                display: 'flex', 
                                alignItems: 'center', 
                                padding: '1.25rem', 
                                backgroundColor: '#ffffff', 
                                borderRadius: '1rem', 
                                boxShadow: '0 4px 15px rgba(19, 27, 46, 0.04)',
                                border: '1px solid #f1f5f9',
                                transition: 'transform 0.2s ease, box-shadow 0.2s ease',
                                cursor: 'pointer'
                            }}
                            onMouseOver={(e) => {
                                e.currentTarget.style.transform = 'translateY(-2px)';
                                e.currentTarget.style.boxShadow = '0 10px 25px rgba(19, 27, 46, 0.08)';
                            }}
                            onMouseOut={(e) => {
                                e.currentTarget.style.transform = 'translateY(0)';
                                e.currentTarget.style.boxShadow = '0 4px 15px rgba(19, 27, 46, 0.04)';
                            }}
                            >
                                <div style={{ 
                                    width: '64px', 
                                    height: '64px', 
                                    borderRadius: '12px', 
                                    backgroundColor: '#f8fafc', 
                                    overflow: 'hidden', 
                                    marginRight: '1.5rem', 
                                    display: 'flex', 
                                    alignItems: 'center', 
                                    justifyContent: 'center',
                                    border: '1px solid #e2e8f0',
                                    flexShrink: 0
                                }}>
                                    {item.image_url ? (
                                        <img src={item.image_url} alt="" style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
                                    ) : (
                                        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#94a3b8" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><rect x="2" y="3" width="20" height="14" rx="2" ry="2"></rect><line x1="8" y1="21" x2="16" y2="21"></line><line x1="12" y1="17" x2="12" y2="21"></line></svg>
                                    )}
                                </div>
                                <div style={{ flex: 1 }}>
                                    <h4 style={{ margin: '0 0 0.3rem 0', fontSize: '1.1rem', color: '#0f172a', fontWeight: '700' }}>{item.name}</h4>
                                    <p style={{ margin: '0', fontSize: '0.85rem', color: '#64748b', display: 'flex', alignItems: 'center', gap: '6px' }}>
                                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect><line x1="16" y1="2" x2="16" y2="6"></line><line x1="8" y1="2" x2="8" y2="6"></line><line x1="3" y1="10" x2="21" y2="10"></line></svg>
                                        {item.date}
                                    </p>
                                </div>
                                <div style={{ textAlign: 'right', display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: '0.5rem' }}>
                                    <span style={{
                                        display: 'inline-flex',
                                        alignItems: 'center',
                                        justifyContent: 'center',
                                        padding: '0.4rem 0.75rem',
                                        borderRadius: '8px',
                                        color: '#fff',
                                        fontWeight: '800',
                                        fontSize: '0.9rem',
                                        backgroundColor: gradeColorMap[item.grade.toLowerCase()] || gradeColorMap.unknown,
                                        boxShadow: '0 2px 5px rgba(0,0,0,0.1)'
                                    }}>
                                        {item.score !== 'unknown' ? item.score : item.grade.toUpperCase()}
                                    </span>
                                </div>
                            </div>
                        ))}
                    </div>
                )}
            </div>
        </div>
    );
}

export default HistoryPage;
