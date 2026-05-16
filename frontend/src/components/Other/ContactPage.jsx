import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import api from '../../api';

function ContactPage() {
  const [formData, setFormData] = useState({ name: '', email: '', message: '' });
  const [status, setStatus] = useState({ submitting: false, success: false, error: null });

  const handleChange = (e) => setFormData(prev => ({ ...prev, [e.target.name]: e.target.value }));

  const handleSubmit = async (e) => {
    e.preventDefault();
    setStatus({ submitting: true, success: false, error: null });
    try {
      const response = await api.post('/api/contact/', formData);
      if (response.data.success) {
        setStatus({ submitting: false, success: true, error: null });
        setFormData({ name: '', email: '', message: '' });
      } else {
        setStatus({ submitting: false, success: false, error: response.data.message || 'Something went wrong.' });
      }
    } catch (err) {
      const errorMsg = err.response?.data?.message || 'Failed to send message. Please try again later.';
      setStatus({ submitting: false, success: false, error: errorMsg });
    }
  };

  return (
    <div className="page-container">
      <motion.h1 className="page-title" initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5 }}>
        Contact Us
      </motion.h1>
      <p style={{ color: 'var(--text-secondary)', marginBottom: 'var(--space-8)', marginTop: '-var(--space-4)' }}>
        We read every message. Expect a reply within 48 hours.
      </p>

      <AnimatePresence mode="wait">
        {status.success ? (
          <motion.div
            key="success"
            className="settings-card"
            style={{ textAlign: 'center', padding: 'var(--space-12)' }}
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0 }}
          >
            <div style={{ fontSize: 48, marginBottom: 'var(--space-4)' }}>✨</div>
            <h3 style={{ fontSize: 'var(--text-xl)', fontWeight: 700, color: 'var(--text-primary)' }}>Message Sent!</h3>
            <p style={{ color: 'var(--text-secondary)', marginTop: 'var(--space-2)' }}>We've received your message and will get back to you soon.</p>
          </motion.div>
        ) : (
          <motion.div key="form" className="contact-card" initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }}>
            <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-4)' }}>
              <input
                type="text" name="name" className="contact-input"
                placeholder="Your Name" value={formData.name}
                onChange={handleChange} required disabled={status.submitting}
              />
              <input
                type="email" name="email" className="contact-input"
                placeholder="name@company.com" value={formData.email}
                onChange={handleChange} required disabled={status.submitting}
              />
              <textarea
                name="message" className="contact-textarea"
                placeholder="Write your message here…" value={formData.message}
                onChange={handleChange} required disabled={status.submitting}
                rows="5"
              />
              {status.error && (
                <motion.div className="auth-error" initial={{ opacity: 0 }} animate={{ opacity: 1 }}>{status.error}</motion.div>
              )}
              <motion.button type="submit" className="contact-submit" disabled={status.submitting} whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.98 }}>
                {status.submitting ? 'Sending…' : 'Send Message'}
              </motion.button>
              <p style={{ fontSize: 'var(--text-xs)', color: 'var(--text-tertiary)', textAlign: 'center' }}>
                No spam. Your message stays private.
              </p>
            </form>
          </motion.div>
        )}
      </AnimatePresence>

      <div style={{ marginTop: 'var(--space-8)', textAlign: 'center' }}>
        <p style={{ fontSize: 'var(--text-sm)', color: 'var(--text-tertiary)' }}>For a faster reply, reach us directly:</p>
        <a href="mailto:se.jaimin91@gmail.com" style={{ color: 'var(--brand-primary)', fontWeight: 600, fontSize: 'var(--text-sm)' }}>
          se.jaimin91@gmail.com
        </a>
      </div>
    </div>
  );
}

export default ContactPage;
