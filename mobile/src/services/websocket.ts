import { useAuthStore } from '../store/authStore';
import { useNetworkStore } from '../store/networkStore';

const WS_URL = __DEV__ ? 'ws://localhost:8000' : 'wss://api.wificinemas.com';
let ws: WebSocket | null = null;
let timer: ReturnType<typeof setTimeout> | null = null;

export function connectWebSocket(shootId: string) {
  const token = useAuthStore.getState().token;
  if (!token) return;
  ws = new WebSocket(`${WS_URL}/ws/metrics/${shootId}?token=${token}`);
  ws.onopen = () => useNetworkStore.getState().setConnected(true);
  ws.onmessage = (e) => {
    const d = JSON.parse(e.data);
    if (d.type === 'metrics') {
      useNetworkStore.getState().setStatus({ shootId: d.shoot_id, isOnline: true, source: d.source, isFailover: d.is_failover, downloadMbps: d.download_mbps, uploadMbps: d.upload_mbps, latencyMs: d.latency_ms, packetLoss: d.packet_loss, connectedDevices: d.connected_devices, lastUpdated: d.timestamp });
    }
  };
  ws.onclose = () => { useNetworkStore.getState().setConnected(false); timer = setTimeout(() => connectWebSocket(shootId), 5000); };
}

export function disconnectWebSocket() { if (timer) clearTimeout(timer); if (ws) { ws.close(); ws = null; } }
