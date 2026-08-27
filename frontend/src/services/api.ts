import axios from 'axios';
import type { HealthResponse } from '../types/api';
import type { Overview, SystemHealth } from '../types/overview';

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000',
});

export const fetchHealth = async (): Promise<HealthResponse> => {
  const response = await api.get<HealthResponse>('/api/health');
  return response.data;
};

export const fetchDatabaseHealth = async (): Promise<HealthResponse> => {
  const response = await api.get<HealthResponse>('/api/health/db');
  return response.data;
};

export const fetchSystemHealth = async (): Promise<SystemHealth> => {
  const response = await api.get<SystemHealth>('/api/health/system');
  return response.data;
};

export const fetchOverview = async (): Promise<Overview> => {
  const response = await api.get<Overview>('/api/overview');
  return response.data;
};
