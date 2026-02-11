import React, { useState } from 'react';
import api from '../api';


function ContactPage() {
    const [formData, setFormData] = useState({
        name: '',
        email: '',
        message: ''
    });
    const [status, setStatus] = useState({
        submitting: false,
        success: false,
        error: null
    });

    const handleChange = (e) => {
        const { name, value } = e.target;
        setFormData(prevState => ({
            ...prevState,
            [name]: value
        }));
    };

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
            console.error('Contact error:', err);
            const errorMsg = err.response?.data?.message || err.response?.data?.errors
                ? Object.values(err.response.data.errors).flat().join(', ')
                : 'Failed to send message. Please try again later.';
            setStatus({ submitting: false, success: false, error: errorMsg });
        }
    };

    return (
        <section className="contact-page">
            <div className="contact-container">
                <div className="contact-hero">
                    <h1 className="contact-title">Contact</h1>
                    <p className="contact-subtitle">We read every message.</p>
                </div>

                <div className="contact-card">
                    {status.success ? (
                        <div className="contact-success">
                            <div className="success-icon">✨</div>
                            <h2>Message Sent!</h2>
                            <p>Thank you for reaching out. We've received your message and will get back to you soon.</p>
                        </div>
                    ) : (
                        <form className="contact-form" onSubmit={handleSubmit}>
                            <div className="form-group">
                                <input
                                    type="text"
                                    name="name"
                                    placeholder="Name"
                                    value={formData.name}
                                    onChange={handleChange}
                                    required
                                    className="form-input"
                                    disabled={status.submitting}
                                />
                            </div>
                            <div className="form-group">
                                <input
                                    type="email"
                                    name="email"
                                    placeholder="Email"
                                    value={formData.email}
                                    onChange={handleChange}
                                    required
                                    className="form-input"
                                    disabled={status.submitting}
                                />
                            </div>
                            <div className="form-group">
                                <textarea
                                    name="message"
                                    placeholder="Message"
                                    value={formData.message}
                                    onChange={handleChange}
                                    required
                                    className="form-input form-textarea"
                                    rows="5"
                                    disabled={status.submitting}
                                ></textarea>
                            </div>

                            {status.error && <p className="form-error">{status.error}</p>}

                            <button
                                type="submit"
                                className={`btn btn-primary ${status.submitting ? 'loading' : ''}`}
                                disabled={status.submitting}
                            >
                                {status.submitting ? 'Sending...' : 'Send message'}
                            </button>

                            <p className="form-footer-note">No spam. Your message stays private.</p>
                        </form>
                    )}
                </div>

                <div className="contact-footer-info">
                    <p>For a faster reply, write to us directly —</p>
                    <a href="mailto:se.jaimin91@gmail.com" className="email-link">se.jaimin91@gmail.com</a>
                </div>
            </div>
        </section>
    );
}

export default ContactPage;
