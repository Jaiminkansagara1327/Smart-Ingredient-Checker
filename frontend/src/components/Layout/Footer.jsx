import React from 'react';

function Footer() {
    const currentYear = new Date().getFullYear();

    return (
        <footer className="footer">
            <div className="footer-content">
                <p className="footer-copyright">
                    © {currentYear} Ingrexa. All rights reserved.
                </p>
                <p className="footer-independence">
                    🛡️ Independent & unbiased — not funded or sponsored by any food company.
                </p>
            </div>
        </footer>
    );
}

export default Footer;
