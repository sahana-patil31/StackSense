import axios from 'axios';
import type { Deployment, Repository } from '../types/ingestion';

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000',
});

export const fetchDeployments = async (): Promise<Deployment[]> => {
  const response = await api.get<Deployment[]>('/api/deployments');
  return response.data;
};

export const fetchRepositories = async (): Promise<Repository[]> => {
  const response = await api.get<Repository[]>('/api/repositories');
  return response.data;
};

export const createRepository = async (payload: Pick<Repository, 'name' | 'provider' | 'default_branch'>): Promise<Repository> => {
  const response = await api.post<Repository>('/api/repositories', payload);
  return response.data;
};