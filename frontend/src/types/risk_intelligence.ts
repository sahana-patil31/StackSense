export interface ContributingFactor {
  factor_name: string;
  feature_value: any;
  impact: 'HIGH' | 'MEDIUM' | 'LOW';
  description: string;
}

export interface DeploymentRiskAnalysis {
  id: string;
  deployment_id: string;
  model_version: string;
  risk_score: number;
  risk_level: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  failure_probability: number;
  feature_snapshot: Record<string, any>;
  contributing_factors: ContributingFactor[];
  created_at: string;
}

export interface Anomaly {
  id: string;
  service_name: string;
  window_start: string;
  window_end: string;
  anomaly_score: number;
  is_anomaly: boolean;
  metrics_snapshot: {
    total_events: number;
    error_count: number;
    critical_count: number;
    warning_count: number;
    error_rate: number;
  };
  detection_method: string;
  created_at: string;
}

export interface EvidenceItem {
  evidence_type: string;
  score: number;
  description: string;
}

export interface RootCauseAnalysis {
  id: string;
  anomaly_id: string;
  candidate_type: string;
  candidate_id: string;
  confidence_score: number;
  evidence: EvidenceItem[];
  created_at: string;
}

export interface Incident {
  id: string;
  title: string;
  status: 'detected' | 'investigating' | 'resolved' | 'closed';
  severity: 'low' | 'medium' | 'high' | 'critical';
  detected_at: string;
  primary_anomaly_id: string;
  probable_cause: string;
  confidence: number;
  created_at: string;
  resolved_at?: string | null;
}
