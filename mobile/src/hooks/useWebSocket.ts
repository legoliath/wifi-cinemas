import { useEffect } from 'react';
import { connectWebSocket, disconnectWebSocket } from '../services/websocket';
export function useWebSocket(shootId: string | undefined) {
  useEffect(() => { if (shootId) { connectWebSocket(shootId); return () => disconnectWebSocket(); } }, [shootId]);
}
