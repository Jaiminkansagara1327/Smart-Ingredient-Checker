import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import api from '../../api';

const GOALS = [
  { id: 'Regular', label: 'Balanced', emoji: '⚖️' },
  { id: 'Weight Loss', label: 'Weight Loss', emoji: '📉' },
  { id: 'Gym', label: 'Muscle Gain', emoji: '💪' },
  { id: 'Heart Health', label: 'Heart Health', emoji: '❤️' },
  { id: 'Weight Gain', label: 'Weight Gain', emoji: '📈' },
  { id: 'Diabetic', label: 'Diabetic', emoji: '🩺' },
];

function SettingsPage({ onNavigate, user, setUser }) {
  const [goal, setGoal] = useState('Regular');
  const [loading, setLoading] = useState(true);
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    const fetchData = async () => {
      try {
        if (user?.health_goal) { setGoal(user.health_goal); }
        else {
          const meRes = await api.get('/api/auth/me/');
          if (meRes.data?.success && meRes.data.user.health_goal) setGoal(meRes.data.user.health_goal);
        }
      } catch (err) { console.error(err); }
      finally { setLoading(false); }
    };
    fetchData();
  }, [user]);

  const handleGoalChange = async (selectedGoal) => {
    setGoal(selectedGoal);
    try {
      await api.patch('/api/auth/me/', { health_goal: selectedGoal });
      if (user) setUser({ ...user, health_goal: selectedGoal });
      setSaved(true); setTimeout(() => setSaved(false), 2000);
    } catch (err) { console.error(err); }
  };

  if (loading) return (
    <div className="page-container">
      <div style={{ display: 'flex', gap: 'var(--space-8)', flexWrap: 'wrap', marginTop: 'var(--space-8)' }}>
        {[1,2,3,4,5,6].map(i => <div key={i} className="skeleton" style={{ width: 120, height: 100, borderRadius: 'var(--radius-xl)' }} />)}
      </div>
    </div>
  );

  return (
    <div className="page-container">
      <motion.h1 className="page-title" initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5 }}>
        Settings
      </motion.h1>

      {/* Profile card */}
      <motion.div className="settings-card" initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1, duration: 0.5 }}>
        <div className="settings-card-header">Profile</div>
        <div className="settings-row">
          <div>
            <div className="settings-label">{user?.first_name || 'User'} {user?.last_name || ''}</div>
            <div className="settings-sub">{user?.email || ''}</div>
          </div>
          <div style={{ width: 48, height: 48, borderRadius: 'var(--radius-full)', background: 'var(--gradient-brand)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 800, color: '#0D1117', fontSize: 'var(--text-xl)' }}>
            {user?.first_name?.[0]?.toUpperCase() || 'U'}
          </div>
        </div>
      </motion.div>

      {/* Health goal */}
      <motion.div className="settings-card" initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.15, duration: 0.5 }}>
        <div className="settings-card-header" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <span>Health Goal</span>
          {saved && <motion.span style={{ fontSize: 'var(--text-xs)', color: 'var(--brand-success)', fontWeight: 600 }} initial={{ opacity: 0 }} animate={{ opacity: 1 }}>✓ Saved</motion.span>}
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(130px, 1fr))', gap: 'var(--space-3)', padding: 'var(--space-5)' }}>
          {GOALS.map((g, i) => (
            <motion.button
              key={g.id}
              onClick={() => handleGoalChange(g.id)}
              style={{
                display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 'var(--space-2)',
                padding: 'var(--space-4)', borderRadius: 'var(--radius-xl)',
                background: goal === g.id ? 'rgba(0,255,135,0.08)' : 'var(--surface-3)',
                border: goal === g.id ? '2px solid rgba(0,255,135,0.35)' : '2px solid var(--border-subtle)',
                cursor: 'pointer', transition: 'all 0.2s',
                color: goal === g.id ? 'var(--brand-primary)' : 'var(--text-secondary)',
                fontWeight: goal === g.id ? 700 : 500, fontSize: 'var(--text-sm)',
              }}
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: i * 0.04 }}
              whileHover={{ scale: 1.03 }} whileTap={{ scale: 0.97 }}
            >
              <span style={{ fontSize: '1.5rem' }}>{g.emoji}</span>
              <span>{g.label}</span>
            </motion.button>
          ))}
        </div>
      </motion.div>
    </div>
  );
}

export default SettingsPage;
