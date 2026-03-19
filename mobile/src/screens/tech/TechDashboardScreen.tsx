/**
 * TechDashboardScreen — Tech at the roulotte. Presses a button to request
 * a snapshot from the roof phone. Sees results + adjustment hint.
 */
import React, { useEffect, useRef, useState } from 'react';
import { View, StyleSheet, Platform } from 'react-native';
import { Text, Surface, Icon, Button, Divider } from 'react-native-paper';
import { useAuthStore } from '../../store/authStore';
import { WS_BASE_URL } from '../../utils/constants';

interface SnapshotResponse {
  telemetry: {
    signal_strength: number;
    obstruction_pct: number;
    tilt_x: number;
    tilt_y: number;
    compass_heading: number;
    latitude: number | null;
    longitude: number | null;
    download_mbps: number;
    upload_mbps: number;
    latency_ms: number;
    phone_battery_pct: number;
    is_charging: boolean;
  };
  hint: {
    action: string;
    direction: string | null;
    magnitude: string | null;
    message: string;
  };
  timestamp: string;
}

const DIRECTION_ARROWS: Record<string, string> = {
  left: '←', right: '→', forward: '↑', backward: '↓',
};

export default function TechDashboardScreen({ route }: any) {
  const shootId = route.params?.shootId;
  const token = useAuthStore((s) => s.token);
  const wsRef = useRef<WebSocket | null>(null);
  const [connected, setConnected] = useState(false);
  const [roofOnline, setRoofOnline] = useState(false);
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState<SnapshotResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!shootId || !token) return;

    const connect = () => {
      const ws = new WebSocket(`${WS_BASE_URL}/ws/roof/${shootId}?token=${token}&role=subscriber`);
      ws.onopen = () => { setConnected(true); setRoofOnline(true); };
      ws.onclose = () => { setConnected(false); setTimeout(connect, 3000); };
      ws.onmessage = (evt) => {
        try {
          const msg = JSON.parse(evt.data);
          if (msg.type === 'snapshot_response') {
            setData(msg);
            setLoading(false);
            setError(null);
          } else if (msg.type === 'error') {
            setError(msg.message);
            setLoading(false);
            setRoofOnline(false);
          }
        } catch {}
      };
      wsRef.current = ws;
    };
    connect();
    return () => { wsRef.current?.close(); };
  }, [shootId, token]);

  const requestSnapshot = () => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      setLoading(true);
      setError(null);
      wsRef.current.send(JSON.stringify({ type: 'request_snapshot' }));
      // Timeout after 10s
      setTimeout(() => setLoading((l) => { if (l) { setError('Timeout — le téléphone-toit ne répond pas'); return false; } return l; }), 10000);
    }
  };

  const t = data?.telemetry;
  const hint = data?.hint;
  const isGood = hint?.action === 'hold';

  return (
    <View style={styles.container}>
      {/* Status */}
      <Surface style={styles.statusBar} elevation={1}>
        <Icon source={connected ? 'wifi' : 'wifi-off'} size={20}
              color={connected ? '#38A169' : '#E53E3E'} />
        <Text style={{ color: '#A0AEC0', marginLeft: 8, flex: 1 }}>
          {connected ? 'Connecté' : 'Reconnexion...'}
        </Text>
      </Surface>

      {/* Request button */}
      <Button
        mode="contained"
        icon="satellite-uplink"
        onPress={requestSnapshot}
        loading={loading}
        disabled={!connected || loading}
        style={styles.requestBtn}
        labelStyle={{ fontSize: 18 }}
      >
        {loading ? 'Lecture en cours...' : 'Vérifier le signal'}
      </Button>

      {error && (
        <Surface style={styles.errorCard} elevation={1}>
          <Text style={{ color: '#FC8181' }}>⚠️ {error}</Text>
        </Surface>
      )}

      {/* Adjustment hint (big card) */}
      {hint && (
        <Surface style={[styles.hintCard, { backgroundColor: isGood ? '#1C4532' : '#742A2A' }]} elevation={3}>
          <Text style={styles.hintArrow}>
            {isGood ? '✅' : DIRECTION_ARROWS[hint.direction || ''] || '⚠️'}
          </Text>
          <Text style={styles.hintMessage}>{hint.message}</Text>
          {hint.magnitude && (
            <Text style={styles.hintMagnitude}>{hint.magnitude.toUpperCase()}</Text>
          )}
        </Surface>
      )}

      {/* Metrics */}
      {t && (
        <>
          <View style={styles.row}>
            <Metric label="Signal" value={`${t.signal_strength}%`}
                    color={t.signal_strength > 70 ? '#38A169' : t.signal_strength > 40 ? '#D69E2E' : '#E53E3E'} />
            <Metric label="Obstruction" value={`${(t.obstruction_pct * 100).toFixed(1)}%`}
                    color={t.obstruction_pct < 0.03 ? '#38A169' : t.obstruction_pct < 0.1 ? '#D69E2E' : '#E53E3E'} />
          </View>
          <View style={styles.row}>
            <Metric label="↓ Download" value={`${t.download_mbps} Mbps`} color="#63B3ED" />
            <Metric label="↑ Upload" value={`${t.upload_mbps} Mbps`} color="#63B3ED" />
          </View>
          <View style={styles.row}>
            <Metric label="Latency" value={`${t.latency_ms} ms`} color="#D69E2E" />
            <Metric label="Heading" value={`${Math.round(t.compass_heading)}°`} color="#A78BFA" />
          </View>

          {/* Battery */}
          <Surface style={styles.battery} elevation={1}>
            <Icon source={t.is_charging ? 'battery-charging' : 'battery'} size={20}
                  color={t.phone_battery_pct > 20 ? '#38A169' : '#E53E3E'} />
            <Text style={{ color: '#A0AEC0', marginLeft: 8 }}>
              Tél-toit : {t.phone_battery_pct}% {t.is_charging ? '⚡' : ''}
            </Text>
          </Surface>

          <Text style={styles.timestamp}>
            Snapshot : {data?.timestamp ? new Date(data.timestamp).toLocaleTimeString() : '—'}
          </Text>
        </>
      )}

      {!data && !loading && !error && (
        <Text style={styles.placeholder}>
          Appuie sur le bouton pour vérifier le positionnement de la dish.
        </Text>
      )}
    </View>
  );
}

function Metric({ label, value, color }: { label: string; value: string; color: string }) {
  return (
    <Surface style={styles.metric} elevation={1}>
      <Text variant="bodySmall" style={{ color: '#A0AEC0' }}>{label}</Text>
      <Text variant="titleMedium" style={{ color, fontFamily: Platform.OS === 'ios' ? 'Menlo' : 'monospace' }}>
        {value}
      </Text>
    </Surface>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#0A0E1A', padding: 16 },
  statusBar: { flexDirection: 'row', alignItems: 'center', padding: 12,
               borderRadius: 8, backgroundColor: '#1A202C', marginBottom: 12 },
  requestBtn: { marginBottom: 16, paddingVertical: 8, borderRadius: 12,
                backgroundColor: '#2B6CB0' },
  errorCard: { padding: 12, borderRadius: 8, backgroundColor: '#1A202C', marginBottom: 12 },
  hintCard: { padding: 24, borderRadius: 16, alignItems: 'center',
              marginBottom: 16, gap: 8 },
  hintArrow: { fontSize: 64 },
  hintMessage: { color: '#FFFFFF', fontSize: 20, fontWeight: '600', textAlign: 'center' },
  hintMagnitude: { color: '#FBD38D', fontSize: 14, fontWeight: '700', letterSpacing: 2 },
  row: { flexDirection: 'row', gap: 12, marginBottom: 12 },
  metric: { flex: 1, padding: 14, borderRadius: 10, backgroundColor: '#1A202C',
            alignItems: 'center', gap: 4 },
  battery: { flexDirection: 'row', alignItems: 'center', padding: 12,
             borderRadius: 8, backgroundColor: '#1A202C', marginTop: 8 },
  timestamp: { color: '#718096', textAlign: 'center', marginTop: 8, fontSize: 12 },
  placeholder: { color: '#718096', textAlign: 'center', marginTop: 40, lineHeight: 22 },
});
