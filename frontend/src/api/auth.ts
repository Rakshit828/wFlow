import { API_BASE } from '../lib/api';

export interface LoginResponse {
  user_id: string;
  email: string;
  created_at: string;
}

/** Redirect browser to Google OAuth login (sets JWT cookies on callback). */
export function redirectToGoogleLogin(): void {
  window.location.href = `${API_BASE}/api/auth/google/login`;
}

/** Build URL to request additional Google scopes (requires existing session). */
export function googleNewScopeUrl(scopes: string[], email: string): string {
  const params = new URLSearchParams();
  scopes.forEach((s) => params.append('scopes', s));
  params.set('email', email);
  return `${API_BASE}/api/integration/google/new-scope?${params.toString()}`;
}
