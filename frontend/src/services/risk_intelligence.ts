import axios from 'axios';
import type {
  Anomaly,
  DeploymentRiskAnalysis,
  Incident,
  RootCauseAnalysis,
} from '../types/risk_intelligence';

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000',
});

// Risk APIs
export const analyzeDeploymentRisk = async (deploymentId: string): Promise<DeploymentRiskAnalysis> => {
  const response = await api.post<DeploymentRiskAnalysis>(`/api/risk/deployments/${deploymentId}/analyze`);
  return response.data;
};

export const fetchDeploymentRisk = async (deploymentId: string): Promise<DeploymentRiskAnalysis> => {
  const response = await api.get<DeploymentRiskAnalysis>(`/api/risk/deployments/${deploymentId}`);
  return response.data;
};

export const fetchRiskAnalyses = async (riskLevel?: string): Promise<DeploymentRiskAnalysis[]> => {
  const response = await api.get<DeploymentRiskAnalysis[]>('/api/risk/deployments', {
    params: { ...(riskLevel ? { risk_level: riskLevel } : {}) },
  });
  return response.data;
};

// Anomaly APIs
export const runAnomalyDetection = async (serviceName?: string, windowMinutes: number = 5): Promise<Anomaly[]> => {
  const response = await api.post<Anomaly[]>('/api/anomalies/detect', null, {
    params: {
      ...(serviceName ? { service_name: serviceName } : {}),
      window_minutes: windowMinutes,
    },
  });
  return response.data;
};

export const fetchAnomalies = async (serviceName?: string, isAnomaly?: boolean): Promise<Anomaly[]> => {
  const response = await api.get<Anomaly[]>('/api/anomalies', {
    params: {
      ...(serviceName ? { service_name: serviceName } : {}),
      ...(isAnomaly !== undefined ? { is_anomaly: isAnomaly } : {}),
    },
  });
  return response.data;
};

export const fetchAnomalyDetails = async (anomalyId: string): Promise<Anomaly> => {
  const response = await api.get<Anomaly>(`/api/anomalies/${anomalyId}`);
  return response.data;
};

// Incident & Root Cause APIs
export const analyzeRootCause = async (anomalyId: string): Promise<RootCauseAnalysis[]> => {
  const response = await api.post<RootCauseAnalysis[]>(`/api/incidents/analyze/${anomalyId}`);
  return response.data;
};

export const fetchIncidents = async (status?: string, severity?: string): Promise<Incident[]> => {
  const response = await api.get<Incident[]>('/api/incidents', {
    params: {
      ...(status ? { status } : {}),
      ...(severity ? { severity } : {}),
    },
  });
  return response.data;
};

export const fetchIncidentDetails = async (incidentId: string): Promise<Incident> => {
  const response = await api.get<Incident>(`/api/incidents/${incidentId}`);
  return response.data;
};
