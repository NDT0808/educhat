import axios from "axios";

const BASE_URL = import.meta.env.VITE_API_BASE_URL || "";

const api = axios.create({
    baseURL: BASE_URL,
    headers: {
        "Content-Type": "application/json",
    },
});

// Request interceptor for API calls
api.interceptors.request.use(
    (config) => {
        const token = localStorage.getItem("accessToken");
        if (token) {
            config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
    },
    (error) => {
        return Promise.reject(error);
    }
);

// Response interceptor for API calls
api.interceptors.response.use(
    (response) => {
        // Add ok property compatible with Fetch API style
        (response as any).ok = response.status >= 200 && response.status < 300;
        return response;
    },
    async (error) => {
        const originalRequest = error.config;
        if (error.response?.status === 401 && !originalRequest._retry) {
            originalRequest._retry = true;
            try {
                const refreshToken = localStorage.getItem("refreshToken");
                if (!refreshToken || refreshToken === "mock_refresh_token") {
                    // No valid refresh token available, just reject
                    return Promise.reject(error);
                }

                const response = await axios.post(`${BASE_URL}/auth/refresh`, {
                    refresh_token: refreshToken,
                });

                const { access_token } = response.data;
                localStorage.setItem("accessToken", access_token);

                api.defaults.headers.common["Authorization"] = `Bearer ${access_token}`;
                return api(originalRequest);
            } catch (refreshError) {
                // Don't redirect to login on refresh failure — let the component handle it
                return Promise.reject(error);
            }
        }
        return Promise.reject(error);
    }
);

export default api;
