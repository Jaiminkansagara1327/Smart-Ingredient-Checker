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

export default api;
