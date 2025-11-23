/**
 * Authentication Store (Zustand)
 * Manages JWT token and user state
 */

import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { User } from '@/types';

interface AuthState {
  token: string | null;
  user: User | null;
  isAuthenticated: boolean;
  setToken: (token: string) => void;
  setUser: (user: User | null) => void;
  logout: () => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      token: null,
      user: null,
      isAuthenticated: false,

      setToken: (token: string) => {
        localStorage.setItem('access_token', token);
        set({ token, isAuthenticated: true });
      },

      setUser: (user: User | null) => {
        set({ user });
      },

      logout: () => {
        localStorage.removeItem('access_token');
        set({ token: null, user: null, isAuthenticated: false });
      },
    }),
    {
      name: 'auth-storage',
      partialize: (state) => ({ token: state.token }),
      onRehydrateStorage: () => (state) => {
        // After rehydration, set isAuthenticated based on token presence
        if (state?.token) {
          state.isAuthenticated = true;
        }
      },
    }
  )
);
