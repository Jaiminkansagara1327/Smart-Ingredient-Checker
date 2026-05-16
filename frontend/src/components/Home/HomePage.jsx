import React, { useState, useEffect, useRef } from 'react';
import { motion, useScroll, useTransform, AnimatePresence } from 'framer-motion';

const fadeUp = {
  hidden: { opacity: 0, y: 32 },
  visible: (delay = 0) => ({ opacity: 1, y: 0, transition: { duration: 0.6, delay, ease: [0.16, 1, 0.3, 1] } }),
};

const FEATURES = [
  {
    icon: '🔬', iconClass: 'red', span: 'bento-span-6',
    title: 'Red-Flag Detection',
    desc: 'Automatic detection of Palm Oil, TBHQ, Hydrogenated fats, artificial colors, and 300+ banned additives.',
    badge: 'DANGER RADAR', badgeClass: 'red',
  },
  {
    icon: '🌱', iconClass: 'green', span: 'bento-span-6',
    title: 'Nutrient Verification',
    desc: 'Mapping whole grains, fiber, micronutrient density, and natural ingredients your body actually needs.',
    badge: 'HEALTH INTEL', badgeClass: 'green',
  },
  {
    icon: '📊', iconClass: 'blue', span: 'bento-span-4',
    title: 'E-Number Library',
    desc: 'EU & Indian standards. Every INS code classified.',
    badge: 'EU STANDARDS', badgeClass: 'blue',
  },
  {
    icon: '🇮🇳', iconClass: 'purple', span: 'bento-span-4',
    title: 'India-First Database',
    desc: 'Specific focus on Indian brands and hidden seed oils.',
    badge: 'MADE FOR INDIA', badgeClass: 'blue',
  },
  {
    icon: '⚡', iconClass: 'green', span: 'bento-span-4',
    title: 'Instant Scoring',
    desc: 'AI-powered health scores in under 3 seconds.',
    badge: 'REAL-TIME', badgeClass: 'green',
  },
];

const STEPS = [
  { num: '01', title: 'Search Product', desc: 'Type any Indian brand name or paste ingredients manually.', active: true },
  { num: '02', title: 'AI Analyzes', desc: 'Our engine cross-references 50,000+ ingredients against global safety databases.', active: false },
  { num: '03', title: 'Make Better Choices', desc: 'Get a detailed health score, red flags, and healthier alternatives.', active: false },
];

function StatCounter({ target, suffix = '' }) {
  const [count, setCount] = useState(0);
  const ref = useRef(null);
  const started = useRef(false);

  useEffect(() => {
    const observer = new IntersectionObserver(([entry]) => {
      if (entry.isIntersecting && !started.current) {
        started.current = true;
        let start = 0;
        const step = target / 60;
        const timer = setInterval(() => {
          start += step;
          if (start >= target) { setCount(target); clearInterval(timer); }
          else setCount(Math.floor(start));
        }, 16);
      }
    }, { threshold: 0.5 });
    if (ref.current) observer.observe(ref.current);
    return () => observer.disconnect();
  }, [target]);

  return <span ref={ref}>{count.toLocaleString()}{suffix}</span>;
}

function RevealSection({ children, delay = 0 }) {
  return (
    <motion.div
      initial="hidden"
      whileInView="visible"
      viewport={{ once: true, margin: '-80px' }}
      custom={delay}
      variants={fadeUp}
    >
      {children}
    </motion.div>
  );
}

function BentoCard({ icon, iconClass, title, desc, badge, badgeClass, span }) {
  return (
    <motion.div
      className={`bento-card ${span}`}
      initial={{ opacity: 0, y: 24 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: '-60px' }}
      transition={{ duration: 0.5, ease: [0.16, 1, 0.3, 1] }}
      whileHover={{ y: -4 }}
    >
      <div className="bento-card-inner">
        <div className={`bento-icon ${iconClass}`}>{icon}</div>
        <h3 className="bento-title">{title}</h3>
        <p className="bento-desc">{desc}</p>
        {badge && <span className={`bento-badge ${badgeClass}`}>{badge}</span>}
      </div>
    </motion.div>
  );
}

function HomePage({ onNavigate, user }) {
  const [showScrollToTop, setShowScrollToTop] = useState(false);
  const heroRef = useRef(null);
  const { scrollYProgress } = useScroll({ target: heroRef, offset: ['start start', 'end start'] });
  const heroOpacity = useTransform(scrollYProgress, [0, 0.7], [1, 0]);
  const heroY = useTransform(scrollYProgress, [0, 1], [0, 80]);

  useEffect(() => {
    const onScroll = () => setShowScrollToTop(window.scrollY > 400);
    window.addEventListener('scroll', onScroll, { passive: true });
    return () => window.removeEventListener('scroll', onScroll);
  }, []);

  return (
    <main className="home-wrap">
      {/* ── HERO ── */}
      <section className="hero-section" ref={heroRef}>
        <div className="hero-bg">
          <div className="hero-glow-1" />
          <div className="hero-glow-2" />
          <div className="hero-grid" />
        </div>

        <motion.div className="hero-content" style={{ opacity: heroOpacity, y: heroY }}>
          <motion.div className="hero-badge" initial={{ opacity: 0, y: -16 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.6, ease: [0.16, 1, 0.3, 1] }}>
            <span className="hero-badge-dot" />
            AI-Powered Ingredient Intelligence for India
          </motion.div>

          <motion.h1 className="hero-title" initial={{ opacity: 0, y: 32 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.7, delay: 0.15, ease: [0.16, 1, 0.3, 1] }}>
            <span className="hero-title-line">EAT</span>
            <span className="hero-title-line gradient">FEARLESSLY.</span>
          </motion.h1>

          <motion.p className="hero-subtitle" initial={{ opacity: 0, y: 24 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.7, delay: 0.25, ease: [0.16, 1, 0.3, 1] }}>
            No sponsors. No bias. Just the absolute truth about what's inside your food — decoded by AI in seconds.
          </motion.p>

          <motion.div className="hero-cta-row" initial={{ opacity: 0, y: 24 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.7, delay: 0.35, ease: [0.16, 1, 0.3, 1] }}>
            <motion.button
              className="btn-primary"
              onClick={() => onNavigate(user ? 'analyze' : 'login')}
              whileHover={{ scale: 1.03, y: -2 }}
              whileTap={{ scale: 0.97 }}
            >
              Start Analyzing Free
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                <path d="M5 12h14M12 5l7 7-7 7" />
              </svg>
            </motion.button>
            <motion.button className="btn-ghost" onClick={() => onNavigate('contact')} whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.98 }}>
              Learn More
            </motion.button>
          </motion.div>

          {/* Stats */}
          <motion.div className="hero-stats" initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ duration: 0.8, delay: 0.5 }}>
            {[
              { num: 50000, suffix: '+', label: 'Ingredients' },
              { num: 300, suffix: '+', label: 'Additives Tracked' },
              { num: 100, suffix: '%', label: 'Unbiased' },
            ].map((stat, i) => (
              <React.Fragment key={stat.label}>
                {i > 0 && <div className="hero-stat-divider" />}
                <div className="hero-stat">
                  <div className="hero-stat-num"><StatCounter target={stat.num} suffix={stat.suffix} /></div>
                  <div className="hero-stat-label">{stat.label}</div>
                </div>
              </React.Fragment>
            ))}
          </motion.div>

          {/* Ingredient preview card */}
          <motion.div className="hero-preview" initial={{ opacity: 0, y: 40 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.8, delay: 0.6 }}>
            <div className="hero-preview-card">
              <div className="preview-header">
                <div className="preview-dot" />
                <span className="preview-label">Live Analysis — Parle-G Biscuits</span>
                <span className="preview-badge">ENGINE V3.4</span>
              </div>
              <div className="preview-body">
                Wheat Flour, Sugar, <span className="ing-red">Refined Palm Oil</span>,{' '}
                Milk Solids, <span className="ing-red">E150c (Caramel Color)</span>,{' '}
                <span className="ing-warn">INS 503(ii)</span>, Salt,{' '}
                <span className="ing-green">Natural Vanilla</span>,{' '}
                <span className="ing-red">Synthetic Flavor</span>.
              </div>
            </div>
          </motion.div>
        </motion.div>
      </section>

      {/* ── FEATURES ── */}
      <section className="section">
        <div className="section-inner">
          <RevealSection>
            <span className="section-label">
              <span>⚡</span> Clinical Intelligence
            </span>
            <h2 className="section-title">Forensic Ingredient Analysis.</h2>
            <p className="section-subtitle">
              We don't give black-box scores. We expose exactly what's in your food — additive by additive.
            </p>
          </RevealSection>

          {/* Bento grid */}
          <div className="bento-grid">
            {/* Big visual card */}
            <motion.div
              className="bento-card bento-span-12"
              initial={{ opacity: 0, y: 24 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, margin: '-60px' }}
              transition={{ duration: 0.5 }}
              whileHover={{ y: -4 }}
            >
              <div className="bento-card-inner">
                <div className="code-visual">
                  <div className="code-header-row">
                    <div className="code-dots">
                      <span className="code-dot r" /><span className="code-dot y" /><span className="code-dot g" />
                    </div>
                    <span className="code-tag">INGREDIENTS ENGINE V3.4</span>
                  </div>
                  Sugar, Wheat Flour,{' '}
                  <span className="hi-red">Palm Oil ⚠</span>, Milk Solids,{' '}
                  <span className="hi-red">E150c (Ammonia Caramel) ⚠</span>,{' '}
                  <span className="hi-warn">INS 503(ii)</span>, Salt,{' '}
                  <span className="hi-green">Natural Vanilla ✓</span>, Lecithin,{' '}
                  <span className="hi-red">Synthetic Flavour ⚠</span>.
                </div>
                <p style={{ fontSize: 'var(--text-xs)', color: 'var(--text-tertiary)', marginTop: 'var(--space-3)' }}>Real-time highlighting engine — every ingredient classified instantly.</p>
              </div>
            </motion.div>

            {FEATURES.map((f, i) => (
              <BentoCard key={i} {...f} />
            ))}
          </div>
        </div>
      </section>

      {/* ── HOW IT WORKS ── */}
      <section className="section" style={{ background: 'var(--surface-1)' }}>
        <div className="section-inner">
          <RevealSection>
            <span className="section-label"><span>🗺️</span> How It Works</span>
            <h2 className="section-title">From Label to Truth<br />in 3 steps.</h2>
          </RevealSection>
          <div className="steps-row">
            {STEPS.map((step, i) => (
              <motion.div
                key={step.num}
                className="step-card"
                initial={{ opacity: 0, y: 32 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true, margin: '-60px' }}
                transition={{ duration: 0.5, delay: i * 0.12, ease: [0.16, 1, 0.3, 1] }}
              >
                <div className={`step-num ${step.active ? 'active' : ''}`}>{step.num}</div>
                <h3 className="step-title">{step.title}</h3>
                <p className="step-desc">{step.desc}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* ── CTA ── */}
      <section className="cta-section">
        <RevealSection>
          <div className="cta-inner">
            <div className="cta-glow" />
            <h2 className="cta-title">Know exactly what you're eating.</h2>
            <p className="cta-sub">Join thousands of Indians making healthier choices every day.</p>
            <div className="cta-actions">
              <motion.button
                className="btn-primary"
                onClick={() => onNavigate(user ? 'analyze' : 'login')}
                whileHover={{ scale: 1.03, y: -2 }}
                whileTap={{ scale: 0.97 }}
              >
                Analyze a Product Free
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M5 12h14M12 5l7 7-7 7" />
                </svg>
              </motion.button>
            </div>
          </div>
        </RevealSection>
      </section>

      {/* Scroll to top */}
      <motion.button
        className={`scroll-top ${showScrollToTop ? 'visible' : ''}`}
        onClick={() => window.scrollTo({ top: 0, behavior: 'smooth' })}
        aria-label="Scroll to top"
        whileHover={{ scale: 1.1 }}
        whileTap={{ scale: 0.9 }}
      >
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
          <polyline points="18 15 12 9 6 15" />
        </svg>
      </motion.button>
    </main>
  );
}

export default HomePage;
