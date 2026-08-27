export interface User {
  id: string;
  email: string;
  role: 'ADMIN' | 'ENGINEER' | 'VIEWER';
  created_at: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: User;
}