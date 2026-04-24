/**
 * utils/nonce.js
 *
 * Cryptographically-strong nonce generator for OAuth flows (finding #8).
 * Uses Web Crypto API — available in all modern browsers and Node ≥ 15.
 */

/**
 * Generate a base64url-encoded 128-bit random nonce.
 * Include this in every Google OIDC request and validate on the backend.
 */
export function generateNonce() {
    const array = new Uint8Array(16); // 128 bits
    crypto.getRandomValues(array);
    // base64url: URL-safe, no padding
    return btoa(String.fromCharCode(...array))
        .replace(/\+/g, '-')
        .replace(/\//g, '_')
        .replace(/=/g, '');
}
