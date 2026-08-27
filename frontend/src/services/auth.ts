import axios from 'axios';
import type { AuthResponse, User } from '../types/auth';

const api = axios.create({ baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000' });

export const login = async (email: string, password: string): Promise<AuthResponse> => {
  const response = await api.post<AuthResponse>('/api/auth/login', { email, password });
  return response.data;
};

export const register = async (email: string, password: string): Promise<AuthResponse> => {
  const response = await api.post<AuthResponse>('/api/auth/register', { email, password });
  return response.data;
};

export const fetchCurrentUser = async (token: string): Promise<User> => {
  const response = await api.get<User>('/api/auth/me', { headers: { Authorization: `Bearer ${token}` } });
  return response.data;
};