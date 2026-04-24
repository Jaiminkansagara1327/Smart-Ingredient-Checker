/**
 * utils/razorpay.js
 *
 * Loads the Razorpay checkout.js script ON DEMAND (finding #9).
 *
 * Why not a static SRI hash?
 *   Razorpay's CDN dynamically generates checkout.js per-request and rotates
 *   it frequently. A static hash would break on every CDN update. Instead we:
 *     1. Load only when the user actually initiates a payment.
 *     2. Restrict via CSP: connect-src and frame-src allow only razorpay.com.
 *     3. Verify Razorpay is PCI-DSS L1 certified; card data never touches us.
 *
 * Usage:
 *   import { loadRazorpay } from '../utils/razorpay';
 *   const Razorpay = await loadRazorpay();
 *   const rzp = new Razorpay({ key: '...', amount: 50000, ... });
 *   rzp.open();
 */

const RAZORPAY_SCRIPT_URL = 'https://checkout.razorpay.com/v1/checkout.js';
let _scriptPromise = null;

export function loadRazorpay() {
    if (_scriptPromise) return _scriptPromise;

    _scriptPromise = new Promise((resolve, reject) => {
        // Already loaded from a previous call
        if (window.Razorpay) {
            resolve(window.Razorpay);
            return;
        }

        const script = document.createElement('script');
        script.src = RAZORPAY_SCRIPT_URL;
        // No crossorigin attribute — Razorpay CDN doesn't send CORS headers
        // for the script itself; SRI is impossible here (see comment above).
        script.onload = () => resolve(window.Razorpay);
        script.onerror = () => {
            _scriptPromise = null; // Allow retry on error
            reject(new Error('Failed to load Razorpay checkout. Please refresh and try again.'));
        };
        document.body.appendChild(script);
    });

    return _scriptPromise;
}
