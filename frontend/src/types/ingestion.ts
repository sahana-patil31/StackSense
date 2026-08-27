export interface Deployment {
  id: string;
  repository_id: string;
  commit_sha: string | null;
  environment: string;
  status: string;
  service_name: string | null;
  deployed_at: string | null;
  created_at: string;
}

export interface Repository {
  id: string;
  name: string;
  url: string | null;
  provider: string;
  default_branch: string | null;
  created_at: string;
  updated_at: string;
}