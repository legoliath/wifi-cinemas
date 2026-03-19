/**
 * RoofMonitorScreen — Phone on the roof. Idles until a snapshot is requested.
 * Reads sensors ONLY when asked, sends one response, goes back to idle.
 * Screen stays awake (kiosk mode).
 */
import React, { useEffect, useRef, useState, useCallback } from 'react';
import { View, StyleSheet, Platform } from 'react-native';
import { Text, Surface, Icon } from 'react-native-paper';
import { activateKeepAwakeAsync, deactivateKeepAwake } from 'expo-keep-awake';
import * as Location from 'expo-location';
import * as Battery from 'expo-battery';
import { Accelerometer, Magnetometer } from 'expo-sensors';
import { useAuthStore } from '../../store/authStore';
import { WS_BASE_URL } from '../../utils/constants';

type Status = 'connecting' | 'idle' | 'reading_sensors' | 'disconnected';

export default function RoofMonitorScreen({ route }: any) {
  const shootId = route.params?.shootId;
  const token = useAuthStore((s) => s.token);
  const wsRef = useRef<WebSocket | null>(null);
  const [status, setStatus] = useState<Status>('connecting');
  const [requestCount, setRequestCount] = useState(0);
  const [lastSent, setLastSent] = useState<string | null>(null);

  // Keep screen awake
  useEffect(() => {
    activateKeepAwakeAsync('roof-monitor');
    return () => { deactivateKeepAwake('roof-monitor'); };
  }, []);

  // Read all sensors once and return a snapshot
  const readSensors = useCallback(async (): Promise<Record<string, any>> => {
    const snapshot: Record<string, any> = {
      source_device: Platform.OS === 'ios' ? 'iPhone' : 'Android',
    };

    // GPS (one-shot)
    try {
      const { status: perm } = await Location.requestForegroundPermissionsAsync();
      if (perm === 'granted') {
        const loc = await Location.getCurrentPositionAsync({ accuracy: Location.Accuracy.High });
        snapshot.latitude = loc.coords.latitude;
        snapshot.longitude = loc.coords.longitude;
        snapshot.altitude_m = loc.coords.altitude;
      }
    } catch {}

    // Battery
    try {
      const level = await Battery.getBatteryLevelAsync();
      const state = await Battery.getBatteryStateAsync();
      snapshot.phone_battery_pct = Math.round(level * 100);
      snapshot.is_charging = state === Battery.BatteryState.CHARGING;
    } catch {}

    // Accelerometer + Magnetometer (quick read)
    await new Promise<void>((resolve) => {
      Accelerometer.setUpdateInterval(200);
      const sub = Accelerometer.addListener(({ x, y }) => {
        snapshot.tilt_x = Math.round(x * 90 * 10) / 10;
        snapshot.tilt_y = Math.round(y * 90 * 10) / 10;
        sub.remove();
        resolve();
      });
      setTimeout(() => { sub.remove(); resolve(); }, 1000); // timeout safety
    });

    await new Promise<void>((resolve) => {
      Magnetometer.setUpdateInterval(200);
      const sub = Magnetometer.addListener(({ x, y }) => {
        let heading = Math.atan2(y, x) * (180 / Math.PI);
        if (heading < 0) heading += 360;
        snapshot.compass_heading = Math.round(heading);
        sub.remove();
        resolve();
      });
      setTimeout(() => { sub.remove(); resolve(); }, 1000);
    });

    return snapshot;
  }, []);

  // WebSocket — idle publisher, responds to requests
  useEffect(() => {
    if (!shootId || !token) return;

    const connect = () => {
      setStatus('connecting');
      const ws = new WebSocket(`${WS_BASE_URL}/ws/roof/${shootId}?token=${token}&role=publisher`);

      ws.onopen = () => setStatus('idle');

      ws.onmessage = async (evt) => {
        try {
          const msg = JSON.parse(evt.data);
          if (msg.type === 'request_snapshot') {
            setStatus('reading_sensors');
            const snapshot = await readSensors();
            ws.send(JSON.stringify({ type: 'snapshot', ...snapshot }));
            setRequestCount((c) => c + 1);
            setLastSent(new Date().toLocaleTimeString());
            setStatus('idle');
          }
        } catch {}
      };

      ws.onclose = () => {
        setStatus('disconnected');
        setTimeout(connect, 5000);
      };

      wsRef.current = ws;
    };

    connect();

    // Heartbeat every 30s to keep connection alive
    const hb = setInterval(() => {
      if (wsRef.current?.readyState === WebSocket.OPEN) {
        wsRef.current.send(JSON.stringify({ type: 'heartbeat' }));
      }
    }, 30000);

    return () => { clearInterval(hb); wsRef.current?.close(); };
  }, [shootId, token, readSensors]);

  const statusConfig = {
    connecting: { icon: 'loading', color: '#D69E2E', label: 'Connexion...' },
    idle: { icon: 'sleep', color: '#38A169', label: 'En attente de demande' },
    reading_sensors: { icon: 'access-point', color: '#63B3ED', label: 'Lecture capteurs...' },
    disconnected: { icon: 'access-point-off', color: '#E53E3E', label: 'Déconnecté — reconnexion...' },
  };

  const cfg = statusConfig[status];

  return (
    <View style={styles.container}>
      <Surface style={styles.card} elevation={2}>
        <Icon source={cfg.icon} size={64} color={cfg.color} />
        <Text variant="headlineMedium" style={[styles.label, { color: cfg.color }]}>
          {cfg.label}
        </Text>
      </Surface>

      <Surface style={styles.stats} elevation={1}>
        <Text style={styles.stat}>📡 Snapshots envoyés : {requestCount}</Text>
        {lastSent && <Text style={styles.stat}>🕐 Dernier : {lastSent}</Text>}
      </Surface>

      <Text style={styles.hint}>
        Ce téléphone attend sur le toit.{'\n'}
        Un technicien peut demander un snapshot à tout moment.
      </Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#0A0E1A', padding: 24, justifyContent: 'center', alignItems: 'center' },
  card: { padding: 40, borderRadius: 20, backgroundColor: '#1A202C', alignItems: 'center', gap: 16, width: '100%' },
  label: { textAlign: 'center', fontWeight: '600' },
  stats: { marginTop: 24, padding: 16, borderRadius: 12, backgroundColor: '#1A202C', width: '100%', gap: 8 },
  stat: { color: '#E2E8F0', fontSize: 16 },
  hint: { color: '#718096', textAlign: 'center', marginTop: 24, lineHeight: 22 },
});
