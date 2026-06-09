import { create } from 'zustand';
import { fetchCurrentUser } from '../api/auth';
import type { UserSession } from '../types/auth';

export type AuthStatus = 'loading' | 'authenticated' | 'unauthenticated';

interface AuthState {
  status: AuthStatus;
  user: UserSession | null;
  checkSession: () => Promise<void>;
  clearSession: () => void;
}

/**
 * Shared promise so that concurrent callers of checkSession()
 * (e.g. React 18 Strict-Mode double-mount) reuse the same
 * in-flight request rather than firing duplicate /api/auth/me calls.
 */
let _checkSessionPromise: Promise<void> | null = null;

export const useAuthStore = create<AuthState>((set, get) => ({
  status: 'loading',
  user: null,

  checkSession: async () => {
    // If a check is already in progress, piggyback on it
    if (_checkSessionPromise) return _checkSessionPromise;

    // If we already resolved to a terminal state, skip the network call
    const { status } = get();
    if (status === 'authenticated' || status === 'unauthenticated') return;

    _checkSessionPromise = (async () => {
      set({ status: 'loading' });
      try {
        const user = (await fetchCurrentUser()).data;
        set({ user, status: 'authenticated' });
      } catch {
        set({ user: null, status: 'unauthenticated' });
      } finally {
        _checkSessionPromise = null;
      }
    })();

    return _checkSessionPromise;
  },

  clearSession: () => {
    set({ user: null, status: 'unauthenticated' });
  },
}));
