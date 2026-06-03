import { apiFetch } from '../lib/api';
import type { UserSession } from '../types/auth';

/** Check whether the browser has a valid session cookie. */
export async function fetchCurrentUser(): Promise<UserSession> {
  return apiFetch<UserSession>('/api/auth/me');
}

/** Redirect browser to Google OAuth login (sets JWT cookies on callback). */
export function redirectToGoogleLogin(): void {
  window.location.href = '/api/auth/google/login';
}

/** Build URL to request additional Google scopes (requires existing session). */
export function googleNewScopeUrl(scopes: string[], email: string): string {
  const params = new URLSearchParams();
  scopes.forEach((s) => params.append('scopes', s));
  params.set('email', email);
  return `/api/integration/google/new-scope?${params.toString()}`;
}
