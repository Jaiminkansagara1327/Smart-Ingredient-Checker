import React from 'react';

function Footer() {
    const currentYear = new Date().getFullYear();

    return (
        <footer className="footer">
            <div className="footer-content">
                <p className="footer-copyright">
                    © {currentYear} Ingrexa. All rights reserved.
                </p>
                <p className="footer-made-with">
                    Made with <span className="heart">❤️</span> by JK for people
                </p>
            </div>
        </footer>
    );
}

export default Footer;
