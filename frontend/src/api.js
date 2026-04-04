import axios from 'axios';

// Create an axios instance with the base URL from environment variables
// If VITE_API_URL is not set (e.g. local dev), it defaults to empty string and uses relative paths (handled by proxy)
const api = axios.create({
    baseURL: import.meta.env.VITE_API_URL || '',
    headers: {
        'Content-Type': 'application/json',
    },
    timeout: 30000, // 30 seconds timeout
});

export const setAuthToken = (token) => {
    if (token) {
        api.defaults.headers.common['Authorization'] = `Bearer ${token}`;
    } else {
        delete api.defaults.headers.common['Authorization'];
    }
};

// Request interceptor to add token
api.interceptors.request.use(
    (config) => {
        const token = localStorage.getItem('access_token');
        if (token) {
            config.headers['Authorization'] = `Bearer ${token}`;
        }
        return config;
    },
    (error) => {
        return Promise.reject(error);
    }
);

// Response interceptor to handle token refresh
api.interceptors.response.use(
    (response) => response,
    async (error) => {
        const originalRequest = error.config;
        
        // If error is 401 and we haven't already tried to refresh
        if (error.response?.status === 401 && !originalRequest._retry) {
            originalRequest._retry = true;
            try {
                const refreshToken = localStorage.getItem('refresh_token');
                if (refreshToken) {
                    const res = await axios.post(`${import.meta.env.VITE_API_URL || ''}/api/auth/token/refresh/`, {
                        refresh: refreshToken
                    });
                    
                    if (res.data.access) {
                        localStorage.setItem('access_token', res.data.access);
                        api.defaults.headers.common['Authorization'] = `Bearer ${res.data.access}`;
                        originalRequest.headers['Authorization'] = `Bearer ${res.data.access}`;
                        return api(originalRequest);
                    }
                }
            } catch (refreshError) {
                // Refresh token is expired too, must log in again
                localStorage.clear();
                window.location.reload(); // Force app to refresh state if not handled by React
            }
        }
        return Promise.reject(error);
    }
);

export default api;
