import { create } from 'zustand';
import type { Shoot } from '../types';

interface ShootState {
  activeShoot: Shoot | null; shoots: Shoot[];
  setActiveShoot: (s: Shoot | null) => void;
  setShoots: (s: Shoot[]) => void;
  addShoot: (s: Shoot) => void;
}

export const useShootStore = create<ShootState>((set) => ({
  activeShoot: null, shoots: [],
  setActiveShoot: (activeShoot) => set({ activeShoot }),
  setShoots: (shoots) => set({ shoots }),
  addShoot: (shoot) => set((s) => ({ shoots: [...s.shoots, shoot] })),
}));
