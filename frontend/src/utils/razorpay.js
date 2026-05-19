/**
 * Loads the Razorpay checkout.js script on demand.
 */

const RAZORPAY_SCRIPT_URL = 'https://checkout.razorpay.com/v1/checkout.js';
let _scriptPromise = null;

/**
 * Loads the Razorpay checkout.js script on demand.
 */
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
        script.onload = () => resolve(window.Razorpay);
        script.onerror = () => {
            _scriptPromise = null;
            reject(new Error('Failed to load Razorpay checkout. Please refresh and try again.'));
        };
        document.body.appendChild(script);
    });

    return _scriptPromise;
}
