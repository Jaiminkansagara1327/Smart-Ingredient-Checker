/**
 * api.js — Secure Axios client
 *
 * Security fixes:
 *  [CRITICAL] #1  – Refresh token NO LONGER stored in localStorage.
 *                   It lives in an HttpOnly cookie set by the backend.
 *  [HIGH]     #2  – Access token stored in module-scoped memory only
 *                   (not localStorage, not sessionStorage).
 *  [HIGH]     #3/4 – Access token is short-lived (15 min); auto-refresh
 *                    via cookie happens transparently.
 */
import axios from 'axios';

// ─── In-memory access token store ────────────────────────────────────────────
// This is the ONLY place the access token is held. An XSS attacker who can
// execute arbitrary JS can still read this, but: (a) the access token is only
// valid for 15 minutes, (b) they cannot read or steal the HttpOnly refresh
// cookie, so they cannot get a new access token once the current one expires.
let _accessToken = null;

export const setAccessToken = (token) => {
    _accessToken = token || null;
};

export const getAccessToken = () => _accessToken;
export const isAuthenticated = () => !!_accessToken;

export const clearAccessToken = () => {
    _accessToken = null;
};

// ─── Axios instance ───────────────────────────────────────────────────────────
const api = axios.create({
    baseURL: import.meta.env.VITE_API_URL || '',
    headers: { 'Content-Type': 'application/json' },
    timeout: 30000,
    // IMPORTANT: send cookies (including the HttpOnly refresh cookie) on
    // same-origin requests and cross-origin requests that explicitly allow it.
    withCredentials: true,
});

// ─── Request interceptor ──────────────────────────────────────────────────────
api.interceptors.request.use(
    (config) => {
        if (_accessToken) {
            config.headers['Authorization'] = `Bearer ${_accessToken}`;
        }
        return config;
    },
    (error) => Promise.reject(error)
);

// ─── Response interceptor (transparent token refresh) ────────────────────────
let _isRefreshing = false;
let _refreshSubscribers = [];

const _subscribeRefresh = (cb) => _refreshSubscribers.push(cb);

const _onRefreshed = (token) => {
    _refreshSubscribers.forEach((cb) => cb(token));
    _refreshSubscribers = [];
};

api.interceptors.response.use(
    (response) => response,
    async (error) => {
        const originalRequest = error.config;

        if (error.response?.status === 401 && !originalRequest._retry) {
            // If we're already refreshing, queue this request
            if (_isRefreshing) {
                return new Promise((resolve) => {
                    _subscribeRefresh((newToken) => {
                        originalRequest.headers['Authorization'] = `Bearer ${newToken}`;
                        resolve(api(originalRequest));
                    });
                });
            }

            originalRequest._retry = true;
            _isRefreshing = true;

            try {
                // The refresh token is sent automatically as an HttpOnly cookie.
                // We POST with withCredentials: true (set globally above).
                const res = await axios.post(
                    `${import.meta.env.VITE_API_URL || ''}/api/auth/token/refresh/`,
                    {},
                    { withCredentials: true }
                );

                if (res.data?.access) {
                    setAccessToken(res.data.access);
                    _onRefreshed(res.data.access);
                    originalRequest.headers['Authorization'] = `Bearer ${res.data.access}`;
                    return api(originalRequest);
                }
            } catch (_refreshError) {
                // Refresh token expired or missing — force re-login
                clearAccessToken();
                // Dispatch a custom event so the React app can redirect cleanly
                window.dispatchEvent(new CustomEvent('ingrexa:session-expired'));
            } finally {
                _isRefreshing = false;
            }
        }

        return Promise.reject(error);
    }
);

export default api;
