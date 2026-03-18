import { create } from 'zustand';
import type { NetworkStatus, MetricPoint } from '../types';

interface NetworkState {
  status: NetworkStatus | null; history: MetricPoint[]; isConnected: boolean;
  setStatus: (s: NetworkStatus) => void;
  addMetric: (m: MetricPoint) => void;
  setConnected: (c: boolean) => void;
}

export const useNetworkStore = create<NetworkState>((set) => ({
  status: null, history: [], isConnected: false,
  setStatus: (status) => set({ status, isConnected: status.isOnline }),
  addMetric: (metric) => set((s) => ({ history: [...s.history.slice(-100), metric] })),
  setConnected: (isConnected) => set({ isConnected }),
}));
