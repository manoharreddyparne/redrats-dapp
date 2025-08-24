import axios, { AxiosRequestConfig, AxiosResponse } from 'axios';

// Base axios instance
const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api',
  headers: { 'Content-Type': 'application/json' },
  withCredentials: true, // <-- important for session-based OAuth
});

// Type for axios responses
export type ApiResponse<T> = AxiosResponse<T>;

// Helper to get token from localStorage
const getToken = (): string | null => {
  if (typeof window !== 'undefined') {
    return localStorage.getItem('redrats_jwt');
  }
  return null;
};

// Unified request object with optional auth
export const request = {
  get: async <T>(
    url: string,
    config?: AxiosRequestConfig,
    auth = true
  ): Promise<ApiResponse<T>> => {
    const headers = auth ? { Authorization: `Bearer ${getToken()}` } : {};
    return api.get<T>(url, { ...config, headers });
  },

  post: async <T, D = unknown>(
    url: string,
    data?: D,
    config?: AxiosRequestConfig,
    auth = true
  ): Promise<ApiResponse<T>> => {
    const headers = auth ? { Authorization: `Bearer ${getToken()}` } : {};
    return api.post<T>(url, data, { ...config, headers });
  },

  put: async <T, D = unknown>(
    url: string,
    data?: D,
    config?: AxiosRequestConfig,
    auth = true
  ): Promise<ApiResponse<T>> => {
    const headers = auth ? { Authorization: `Bearer ${getToken()}` } : {};
    return api.put<T>(url, data, { ...config, headers });
  },

  delete: async <T>(
    url: string,
    config?: AxiosRequestConfig,
    auth = true
  ): Promise<ApiResponse<T>> => {
    const headers = auth ? { Authorization: `Bearer ${getToken()}` } : {};
    return api.delete<T>(url, { ...config, headers });
  },
};

export default api;
