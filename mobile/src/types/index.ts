export interface User { id: string; email: string; name: string; phone?: string; role: 'admin' | 'user'; lang: 'fr' | 'en'; isActive: boolean; createdAt: string; }
export interface Shoot { id: string; name: string; ssid: string; client: string; location?: string; startDate: string; endDate?: string; kitId?: string; status: 'scheduled' | 'active' | 'completed' | 'cancelled'; createdBy: string; createdAt: string; }
export type NetworkSource = 'starlink' | '5g' | 'both';
export interface NetworkStatus { shootId: string; isOnline: boolean; source: NetworkSource; isFailover: boolean; downloadMbps: number; uploadMbps: number; latencyMs: number; packetLoss: number; connectedDevices: number; lastUpdated: string; }
export interface MetricPoint { timestamp: string; downloadMbps: number; uploadMbps: number; latencyMs: number; packetLoss: number; source: NetworkSource; isFailover: boolean; }
export interface Device { id: string; mac: string; hostname?: string; userName?: string; apName?: string; connectedAt: string; }
export type AlertSeverity = 'info' | 'warning' | 'critical';
export interface Alert { id: string; shootId: string; type: string; severity: AlertSeverity; message: string; acknowledged: boolean; createdAt: string; }
export interface TokenResponse { accessToken: string; tokenType: string; expiresIn: number; userId: string; role: string; }
export interface AccessCode { code: string; qrData: string; shootId: string; }
