/**
 * Cryptographically-strong nonce generator for OAuth flows.
 * Uses Web Crypto API.
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
