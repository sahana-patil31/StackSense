export interface CodeFile {
  id: string;
  repository_id: string;
  path: string;
  language: string;
  size: number;
  analysis_status: 'success' | 'error' | 'pending';
  analysis_error?: string | null;
  analyzed_at: string;
}

export interface CodeEntity {
  id: string;
  repository_id: string;
  file_id: string;
  parent_entity_id?: string | null;
  entity_type: 'FILE' | 'MODULE' | 'CLASS' | 'FUNCTION' | 'METHOD';
  name: string;
  qualified_name?: string | null;
  start_line: number;
  end_line: number;
}

export interface CodeRelationship {
  id: string;
  repository_id: string;
  source_entity_id: string;
  target_entity_id?: string | null;
  relationship_type: 'CONTAINS' | 'IMPORTS' | 'CALLS' | 'DEFINES';
  resolved: boolean;
  raw_target?: string | null;
}

export interface AnalysisRun {
  id: string;
  repository_id: string;
  status: 'pending' | 'running' | 'completed' | 'failed' | 'partial';
  files_discovered: number;
  files_analyzed: number;
  entities_found: number;
  relationships_found: number;
  files_failed: number;
  started_at: string;
  completed_at?: string | null;
  error_summary?: string | null;
}

export interface GraphNode {
  id: string;
  label: string;
  type: string;
  file_id?: string | null;
  file_path?: string | null;
  name: string;
  qualified_name?: string | null;
  start_line?: number | null;
  end_line?: number | null;
}

export interface GraphEdge {
  id: string;
  source: string;
  target: string;
  relationship_type: string;
  resolved: boolean;
  raw_target?: string | null;
}

export interface GraphData {
  nodes: GraphNode[];
  edges: GraphEdge[];
}
