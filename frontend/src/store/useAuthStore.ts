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

export const useAuthStore = create<AuthState>((set) => ({
  status: 'loading',
  user: null,

  checkSession: async () => {
    set({ status: 'loading' });
    try {
      const user = await fetchCurrentUser();
      set({ user, status: 'authenticated' });
    } catch {
      set({ user: null, status: 'unauthenticated' });
    }
  },

  clearSession: () => {
    set({ user: null, status: 'unauthenticated' });
  },
}));
