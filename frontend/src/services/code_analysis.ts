import axios from 'axios';
import type {
  AnalysisRun,
  CodeEntity,
  CodeFile,
  CodeRelationship,
  GraphData,
} from '../types/code_analysis';

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000',
});

export const triggerRepositoryAnalysis = async (
  repositoryId: string,
  localPath?: string
): Promise<AnalysisRun> => {
  const response = await api.post<AnalysisRun>(
    `/api/code-analysis/repositories/${repositoryId}/analyze`,
    { path: localPath || null }
  );
  return response.data;
};

export const fetchAnalyzedFiles = async (repositoryId: string): Promise<CodeFile[]> => {
  const response = await api.get<CodeFile[]>(
    `/api/code-analysis/repositories/${repositoryId}/files`
  );
  return response.data;
};

export const fetchCodeEntities = async (
  repositoryId: string,
  entityType?: string,
  fileId?: string,
  name?: string
): Promise<CodeEntity[]> => {
  const response = await api.get<CodeEntity[]>(
    `/api/code-analysis/repositories/${repositoryId}/entities`,
    {
      params: {
        ...(entityType ? { entity_type: entityType } : {}),
        ...(fileId ? { file_id: fileId } : {}),
        ...(name ? { name } : {}),
      },
    }
  );
  return response.data;
};

export const fetchCodeRelationships = async (
  repositoryId: string,
  relationshipType?: string
): Promise<CodeRelationship[]> => {
  const response = await api.get<CodeRelationship[]>(
    `/api/code-analysis/repositories/${repositoryId}/relationships`,
    {
      params: {
        ...(relationshipType ? { relationship_type: relationshipType } : {}),
      },
    }
  );
  return response.data;
};

export const fetchRepositoryGraph = async (repositoryId: string): Promise<GraphData> => {
  const response = await api.get<GraphData>(
    `/api/code-analysis/repositories/${repositoryId}/graph`
  );
  return response.data;
};

export const fetchAnalysisRun = async (runId: string): Promise<AnalysisRun> => {
  const response = await api.get<AnalysisRun>(`/api/code-analysis/runs/${runId}`);
  return response.data;
};
