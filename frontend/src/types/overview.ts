export interface SystemHealth {
  status: string;
  api: string;
  database: string;
  vector_search: string;
  risk_model: string;
  embedding_provider: string;
  llm: string;
}

export interface Overview {
  repositories: number;
  commits: number;
  deployments: number;
  events: number;
  active_incidents: number;
  anomalies: number;
  high_risk_deployments: number;
  recent_commits: { id: string; message: string; sha: string }[];
  recent_deployments: { id: string; service_name: string; status: string }[];
  recent_events: { id: string; message: string; severity: string }[];
}