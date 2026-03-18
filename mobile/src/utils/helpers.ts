export function formatSpeed(mbps: number): string { return mbps >= 1000 ? `${(mbps/1000).toFixed(1)} Gbps` : `${mbps.toFixed(1)} Mbps`; }
export function formatLatency(ms: number): string { return `${ms.toFixed(0)} ms`; }
export function formatPacketLoss(pct: number): string { return `${pct.toFixed(1)}%`; }
export function getConnectionColor(isOnline: boolean, isFailover: boolean): string { if (!isOnline) return '#EF4444'; if (isFailover) return '#F97316'; return '#10B981'; }
export function parseQRCode(data: string): { shootId: string; code: string } | null { const m = data.match(/^wfc:\/\/([^/]+)\/(.+)$/); return m ? { shootId: m[1], code: m[2] } : null; }
