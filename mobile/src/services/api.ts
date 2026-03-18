import axios from 'axios';
import { useAuthStore } from '../store/authStore';

const API_URL = __DEV__ ? 'http://localhost:8000/api/v1' : 'https://api.wificinemas.com/api/v1';
export const api = axios.create({ baseURL: API_URL, timeout: 15000, headers: { 'Content-Type': 'application/json' } });

api.interceptors.request.use((config) => {
  const token = useAuthStore.getState().token;
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

api.interceptors.response.use((r) => r, (error) => {
  if (error.response?.status === 401) useAuthStore.getState().logout();
  return Promise.reject(error);
});

export default api;
