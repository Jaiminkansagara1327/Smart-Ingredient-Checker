import React, { useState, useEffect } from 'react';
import api from '../../api';
import '../Auth/AuthPremium.css';

const AI_PROVIDER_KEY = 'ingrexa_ai_provider';

const aiProviders = [
    {
        value: 'auto',
        label: 'Auto',
        description: 'Best available model selected automatically',
        icon: (
            <svg width="24" height="24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <circle cx="12" cy="12" r="10"/>
                <path d="M12 8v4l3 3"/>
            </svg>
        ),
    },
    {
        value: 'openai',
        label: 'GPT-4o',
        description: 'OpenAI — strong for complex ingredient reasoning',
        icon: (
            <svg width="24" height="24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M12 2L2 7l10 5 10-5-10-5z"/><path d="M2 17l10 5 10-5"/><path d="M2 12l10 5 10-5"/>
            </svg>
        ),
    },
    {
        value: 'gemini',
        label: 'Gemini',
        description: 'Google Gemini — great for detailed health scoring',
        icon: (
            <svg width="24" height="24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/>
            </svg>
        ),
    },
];

function SettingsPage({ onNavigate, user, setUser }) {
    const [goal, setGoal] = useState('Regular');
    const [loading, setLoading] = useState(true);
    const [aiProvider, setAiProvider] = useState(() => localStorage.getItem(AI_PROVIDER_KEY) || 'auto');

    const goals = [
        { id: 'Regular', label: 'Balanced', icon: <svg width="24" height="24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M20.59 13.41l-7.17 7.17a2 2 0 0 1-2.83 0L2 12V2h10l8.59 8.59a2 2 0 0 1 0 2.82z"></path><line x1="7" y1="7" x2="7.01" y2="7"></line></svg> },
        { id: 'Weight Loss', label: 'Weight Loss', icon: <svg width="24" height="24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polyline points="23 18 13.5 8.5 8.5 13.5 1 6"></polyline><polyline points="17 18 23 18 23 12"></polyline></svg> },
        { id: 'Gym', label: 'Muscle Gain', icon: <svg width="24" height="24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"></polygon></svg> },
        { id: 'Heart Health', label: 'Heart Health', icon: <svg width="24" height="24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"></path></svg> },
        { id: 'Weight Gain', label: 'Weight Gain', icon: <svg width="24" height="24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M12 5v14M5 12h14"></path></svg> },
        { id: 'Diabetic', label: 'Diabetic', icon: <svg width="24" height="24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M21.5 2v6h-6M21.34 15.57a10 10 0 1 1-.59-9.21l-5.42 5.42"></path></svg> }
    ];

    useEffect(() => {
        const fetchSettingsData = async () => {
            try {
                if (user && user.health_goal) {
                    setGoal(user.health_goal);
                } else {
                    const meRes = await api.get('/api/auth/me/');
                    if (meRes.data?.success && meRes.data.user.health_goal) {
                        setGoal(meRes.data.user.health_goal);
                    }
                }
            } catch (err) {
                console.error("Failed to load settings data", err);
            } finally {
                setLoading(false);
            }
        };
        fetchSettingsData();
    }, [user]);

    const handleGoalChange = async (selectedGoal) => {
        setGoal(selectedGoal);
        try {
            await api.patch('/api/auth/me/', { health_goal: selectedGoal });
            if (user) setUser({ ...user, health_goal: selectedGoal });
        } catch (err) {
            console.error("Failed to update goal", err);
        }
    };

    const handleProviderChange = (value) => {
        setAiProvider(value);
        localStorage.setItem(AI_PROVIDER_KEY, value);
    };

    const dividerStyle = { borderBottom: '1px solid #e2e7ff', margin: '2rem 0' };
    const sectionTitleStyle = { fontSize: '1.2rem', marginBottom: '0.5rem', color: 'var(--color-text-primary)', fontWeight: '700' };
    const sectionSubtitleStyle = { fontSize: '0.875rem', color: 'var(--color-text-secondary)', marginBottom: '1.25rem' };

    return (
        <div className="auth-container" style={{ padding: '2rem 1rem', maxWidth: '800px', margin: '0 auto' }}>
            <div className="auth-card" style={{ padding: '2rem', marginTop: '2rem' }}>

                {/* ── Profile header ── */}
                <div style={{ display: 'flex', alignItems: 'center', marginBottom: '2rem' }}>
                    <div style={{
                        width: '64px', height: '64px', borderRadius: '50%',
                        backgroundColor: 'var(--color-primary, #00A389)', color: 'white',
                        display: 'flex', alignItems: 'center', justifyContent: 'center',
                        fontSize: '1.5rem', fontWeight: '600', marginRight: '1rem',
                        flexShrink: 0,
                    }}>
                        {user?.first_name ? user.first_name[0].toUpperCase() : 'U'}
                    </div>
                    <div>
                        <h2 style={{ fontSize: '1.5rem', margin: '0', fontWeight: 'bold', color: 'var(--color-text-primary)' }}>
                            {user?.first_name || 'User'} {user?.last_name || ''}
                        </h2>
                        <p style={{ margin: '0', color: 'var(--color-text-secondary, #666)' }}>{user?.email || 'user@example.com'}</p>
                        <span style={{ fontSize: '0.75rem', backgroundColor: '#eef0ff', color: '#00A389', padding: '0.2rem 0.6rem', borderRadius: '1rem', fontWeight: 'bold', display: 'inline-block', marginTop: '0.5rem' }}>Premium Profile</span>
                    </div>
                </div>

                <div style={dividerStyle} />

                {/* ── Health Goal ── */}
                <h3 style={sectionTitleStyle}>Current Goal</h3>
                <p style={sectionSubtitleStyle}>Personalizes how ingredients are scored for your body.</p>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))', gap: '1rem', marginBottom: '2rem' }}>
                    {goals.map(g => (
                        <button
                            key={g.id}
                            onClick={() => handleGoalChange(g.id)}
                            style={{
                                display: 'flex', flexDirection: 'column', alignItems: 'center',
                                padding: '1rem', borderRadius: '1rem', cursor: 'pointer',
                                transition: 'all 0.2s',
                                backgroundColor: goal === g.id ? '#f4fffa' : '#f2f3ff',
                                border: goal === g.id ? '2px solid #00A389' : '2px solid transparent',
                                color: goal === g.id ? '#006857' : 'var(--color-text-primary)',
                                fontWeight: goal === g.id ? 'bold' : 'normal',
                            }}
                        >
                            <span style={{ fontSize: '1.5rem', marginBottom: '0.5rem' }}>{g.icon}</span>
                            <span style={{ fontSize: '0.9rem' }}>{g.label}</span>
                        </button>
                    ))}
                </div>

                <div style={dividerStyle} />

                {/* ── AI Analysis Engine ── */}
                <h3 style={sectionTitleStyle}>AI Analysis Engine</h3>
                <p style={sectionSubtitleStyle}>Choose which AI model powers ingredient analysis. Your preference is saved locally.</p>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '1rem', marginBottom: '1rem' }}>
                    {aiProviders.map(p => {
                        const isActive = aiProvider === p.value;
                        return (
                            <button
                                key={p.value}
                                onClick={() => handleProviderChange(p.value)}
                                style={{
                                    display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '0.5rem',
                                    padding: '1.25rem 1rem', borderRadius: '1rem', cursor: 'pointer',
                                    transition: 'all 0.2s',
                                    backgroundColor: isActive ? '#eef0ff' : '#f2f3ff',
                                    border: isActive ? '2px solid var(--color-accent-primary, #4f46e5)' : '2px solid transparent',
                                    color: isActive ? 'var(--color-accent-primary, #4f46e5)' : 'var(--color-text-primary)',
                                    fontWeight: isActive ? '700' : '500',
                                    textAlign: 'center',
                                }}
                            >
                                <span style={{ color: isActive ? 'var(--color-accent-primary, #4f46e5)' : 'var(--color-text-secondary)' }}>
                                    {p.icon}
                                </span>
                                <span style={{ fontSize: '1rem' }}>{p.label}</span>
                                <span style={{ fontSize: '0.75rem', color: isActive ? 'var(--color-accent-primary, #4f46e5)' : 'var(--color-text-tertiary)', fontWeight: '400', lineHeight: '1.3' }}>
                                    {p.description}
                                </span>
                            </button>
                        );
                    })}
                </div>

            </div>
        </div>
    );
}

export default SettingsPage;
