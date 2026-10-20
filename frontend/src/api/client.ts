import axios from 'axios';

// URL del backend: VITE_API_URL (ej: http://localhost:8000 en desarrollo).
// Si no está definida se usa el backend desplegado en Render.
const API_URL = import.meta.env.VITE_API_URL || 'https://turnos-y-reservas.onrender.com';

export const apiClient = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);
