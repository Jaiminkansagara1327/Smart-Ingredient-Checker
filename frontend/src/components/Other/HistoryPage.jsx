import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import api from '../../api';

function HistoryPage({ onNavigate, user, onSelectHistoryItem }) {
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchHistory = async () => {
      try {
        const histRes = await api.get('/api/history/');
        if (histRes.data?.success && histRes.data.items) {
          const mapped = histRes.data.items.map(item => {
            let finalName = item.product_name;
            if (!finalName || ['Analyzed Product', 'Unknown'].includes(finalName.trim())) {
              finalName = item.analysis_json?._product_meta?.name || item.analysis_json?.product_info?.name || item.analysis_json?.product?.name;
            }
            if (!finalName || ['Analyzed Product', 'Unknown'].includes(finalName.trim())) {
              if (item.input_text_preview) {
                const snippet = item.input_text_preview.length > 50 ? item.input_text_preview.substring(0, 47) + '...' : item.input_text_preview;
                finalName = item.input_method === 'text' ? snippet : `Missing Name (${snippet})`;
              } else finalName = item.input_method === 'text' ? 'Custom Label' : 'Unknown Scan';
            }
            return {
              name: finalName,
              score: (item.score !== null && item.score !== undefined) ? Number(item.score).toFixed(1) : (item.nutriscore_grade ? item.nutriscore_grade.toUpperCase() : 'N/A'),
              grade: item.nutriscore_grade || 'unknown',
              image_url: item.analysis_json?.product?.image_url || item.analysis_json?.product_info?.image_url || item.analysis_json?.image_url || '',
              date: new Date(item.created_at).toLocaleDateString('en-IN', { year: 'numeric', month: 'short', day: 'numeric' }),
              analysis_json: item.analysis_json,
            };
          });
          setHistory(mapped);
        }
      } catch (err) { console.error(err); }
      finally { setLoading(false); }
    };
    fetchHistory();
  }, []);

  const scoreColor = (grade) => {
    const map = { a: 'var(--brand-success)', b: '#85C441', c: 'var(--brand-warning)', d: '#EE8100', e: 'var(--brand-danger)', unknown: 'var(--text-tertiary)' };
    return map[grade?.toLowerCase()] || map.unknown;
  };

  return (
    <div className="page-container">
      <motion.h1 className="page-title" initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5 }}>
        Intelligence Log
      </motion.h1>

      {loading ? (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-3)' }}>
          {[1, 2, 3, 4].map(i => (
            <div key={i} className="history-item" style={{ cursor: 'default' }}>
              <div className="skeleton" style={{ width: 52, height: 52, borderRadius: 'var(--radius-lg)', flexShrink: 0 }} />
              <div style={{ flex: 1 }}>
                <div className="skeleton" style={{ height: 14, width: '60%' }} />
                <div className="skeleton" style={{ height: 11, width: '30%', marginTop: 8 }} />
              </div>
            </div>
          ))}
        </div>
      ) : history.length === 0 ? (
        <motion.div className="empty-state" initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }}>
          <div className="empty-icon">📂</div>
          <h3 className="empty-title">No Analyses Yet</h3>
          <p className="empty-sub">Start by analyzing a product label.</p>
          <motion.button
            className="btn-primary"
            onClick={() => onNavigate('analyze')}
            style={{ marginTop: 'var(--space-6)', fontSize: 'var(--text-sm)', padding: 'var(--space-3) var(--space-6)' }}
            whileHover={{ scale: 1.03 }} whileTap={{ scale: 0.97 }}
          >
            Analyze a Product
          </motion.button>
        </motion.div>
      ) : (
        <div className="history-grid">
          {history.map((item, idx) => (
            <motion.div
              key={idx} className="history-item"
              onClick={() => onSelectHistoryItem?.(item)}
              initial={{ opacity: 0, y: 16 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: idx * 0.05, duration: 0.4 }}
              whileHover={{ x: 4 }}
            >
              <div className="history-img">
                {item.image_url ? <img src={item.image_url} alt="" loading="lazy" /> : (
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="var(--text-tertiary)" strokeWidth="1.5"><path d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4" /></svg>
                )}
              </div>
              <div className="history-info">
                <div className="history-name">{item.name}</div>
                <div className="history-brand">{item.date}</div>
              </div>
              <span style={{ padding: '4px 12px', borderRadius: 'var(--radius-full)', fontSize: 'var(--text-xs)', fontWeight: 700, background: `${scoreColor(item.grade)}20`, color: scoreColor(item.grade), flexShrink: 0 }}>
                {item.score !== 'unknown' ? item.score : item.grade.toUpperCase()}
              </span>
            </motion.div>
          ))}
        </div>
      )}
    </div>
  );
}

export default HistoryPage;
