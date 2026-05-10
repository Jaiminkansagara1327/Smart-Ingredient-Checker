import axios from 'axios';

let _accessToken = null;

export const setAccessToken = (token) => { _accessToken = token || null; };
export const getAccessToken = () => _accessToken;
export const isAuthenticated = () => !!_accessToken;
export const clearAccessToken = () => { _accessToken = null; };

const api = axios.create({
    baseURL: import.meta.env.VITE_API_URL || '',
    headers: { 'Content-Type': 'application/json' },
    timeout: 30000,
    withCredentials: true,
});

api.interceptors.request.use(
    (config) => {
        if (_accessToken) config.headers['Authorization'] = `Bearer ${_accessToken}`;
        return config;
    },
    (error) => Promise.reject(error)
);

let _isRefreshing = false;
let _refreshQueue = [];

api.interceptors.response.use(
    (response) => response,
    async (error) => {
        const req = error.config;

        if (error.response?.status === 401 && !req._retry) {
            if (_isRefreshing) {
                return new Promise((resolve) => {
                    _refreshQueue.push((token) => {
                        req.headers['Authorization'] = `Bearer ${token}`;
                        resolve(api(req));
                    });
                });
            }

            req._retry = true;
            _isRefreshing = true;

            try {
                const res = await axios.post(
                    `${import.meta.env.VITE_API_URL || ''}/api/auth/token/refresh/`,
                    {},
                    { withCredentials: true }
                );

                if (res.data?.access) {
                    setAccessToken(res.data.access);
                    _refreshQueue.forEach((cb) => cb(res.data.access));
                    _refreshQueue = [];
                    req.headers['Authorization'] = `Bearer ${res.data.access}`;
                    return api(req);
                }
            } catch {
                clearAccessToken();
                window.dispatchEvent(new CustomEvent('ingrexa:session-expired'));
            } finally {
                _isRefreshing = false;
            }
        }

        return Promise.reject(error);
    }
);

export default api;
