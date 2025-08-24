// src/lib/auth.ts
import api from './api';
import { AxiosRequestConfig, AxiosResponse, AxiosError } from 'axios';

const TOKEN_KEY = 'redrats_jwt';
const REFRESH_KEY = 'redrats_refresh';

// --- Token helpers ---
export const setToken = (token: string) => localStorage.setItem(TOKEN_KEY, token);
export const getToken = () => localStorage.getItem(TOKEN_KEY);
export const removeToken = () => localStorage.removeItem(TOKEN_KEY);

export const setRefreshToken = (token: string) => localStorage.setItem(REFRESH_KEY, token);
export const getRefreshToken = () => localStorage.getItem(REFRESH_KEY);
export const removeRefreshToken = () => localStorage.removeItem(REFRESH_KEY);

// --- Authentication check ---
export const isAuthenticated = () => !!getToken();

// --- Logout helper ---
export const logout = () => {
  removeToken();
  removeRefreshToken();
  console.log("Logged out successfully. Tokens cleared.");
};

// --- Refresh access token using refresh token ---
export const refreshToken = async (): Promise<string | null> => {
  const refresh = getRefreshToken();
  if (!refresh) return null;

  try {
    const res = await api.post<{ access: string }>('/users/token/refresh/', { refresh });
    setToken(res.data.access);
    return res.data.access;
  } catch {
    logout();
    return null;
  }
};

// --- Authenticated API wrapper (JWT only) ---
export const authApi = {
  get: async <T>(url: string, config?: AxiosRequestConfig): Promise<AxiosResponse<T>> => {
    let token = getToken();
    if (!token) throw new Error("No access token found. This endpoint requires JWT.");

    console.log("Sending GET (JWT) to", url);

    try {
      return await api.get<T>(url, { 
        ...config, 
        headers: { ...(config?.headers || {}), Authorization: `Bearer ${token}` },
        withCredentials: true
      });
    } catch (err: unknown) {
      if (isAxiosUnauthorized(err)) {
        token = await refreshToken();
        if (!token) throw err;
        return api.get<T>(url, { 
          ...config, 
          headers: { ...(config?.headers || {}), Authorization: `Bearer ${token}` },
          withCredentials: true
        });
      }
      throw err;
    }
  },

  post: async <T, D = unknown>(url: string, data?: D, config?: AxiosRequestConfig): Promise<AxiosResponse<T>> => {
    let token = getToken();
    if (!token) throw new Error("No access token found. This endpoint requires JWT.");

    console.log("Sending POST (JWT) to", url);

    try {
      return await api.post<T>(url, data, { 
        ...config, 
        headers: { ...(config?.headers || {}), Authorization: `Bearer ${token}` },
        withCredentials: true
      });
    } catch (err: unknown) {
      if (isAxiosUnauthorized(err)) {
        token = await refreshToken();
        if (!token) throw err;
        return api.post<T>(url, data, { 
          ...config, 
          headers: { ...(config?.headers || {}), Authorization: `Bearer ${token}` },
          withCredentials: true
        });
      }
      throw err;
    }
  },
};

// --- Session API wrapper (no JWT, just cookies + headers) ---
export const sessionApi = {
  get: async <T>(url: string, config?: AxiosRequestConfig): Promise<AxiosResponse<T>> => {
    console.log("Sending GET (session) to", url);
    return api.get<T>(url, { ...config, withCredentials: true });
  },

  post: async <T, D = unknown>(url: string, data?: D, config?: AxiosRequestConfig): Promise<AxiosResponse<T>> => {
    console.log("Sending POST (session) to", url);
    return api.post<T>(url, data, { ...config, withCredentials: true });
  },
};

// --- Type guard helper ---
function isAxiosUnauthorized(err: unknown): boolean {
  if (err instanceof AxiosError) {
    return err.response?.status === 401;
  }
  return false;
}
