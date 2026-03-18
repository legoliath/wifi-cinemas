import { create } from 'zustand';
import type { User } from '../types';

interface AuthState {
  user: User | null; token: string | null; isAuthenticated: boolean; isLoading: boolean;
  setAuth: (token: string, user: User) => void;
  logout: () => void;
  setLoading: (l: boolean) => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null, token: null, isAuthenticated: false, isLoading: true,
  setAuth: (token, user) => set({ token, user, isAuthenticated: true, isLoading: false }),
  logout: () => set({ token: null, user: null, isAuthenticated: false, isLoading: false }),
  setLoading: (isLoading) => set({ isLoading }),
}));
