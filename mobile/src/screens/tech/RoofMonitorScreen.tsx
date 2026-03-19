/**
 * RoofMonitorScreen — "Kiosk mode" for the phone mounted on the roof.
 * Reads sensors (accelerometer, GPS, compass) and streams telemetry
 * to the backend via WebSocket. Screen stays awake.
 */
import React, { useEffect, useRef, useState } from 'react';
import { View, StyleSheet, Platform } from 'react-native';
import { Text, Surface, Icon, ProgressBar } from 'react-native-paper';
import { activateKeepAwakeAsync, deactivateKeepAwake } from 'expo-keep-awake';
import * as Location from 'expo-location';
import * as Battery from 'expo-battery';
import { Accelerometer, Magnetometer } from 'expo-sensors';
import { useAuthStore } from '../../store/authStore';
import { API_BASE_URL, WS_BASE_URL } from '../../utils/constants';

interface TelemetryState {
  signal_strength: number;
  obstruction_pct: number;
  tilt_x: number;
  tilt_y: number;
  compass_heading: number;
  latitude: number | null;
  longitude: number | null;
  altitude_m: number | null;
  download_mbps: number;
  upload_mbps: number;
  latency_ms: number;
  phone_battery_pct: number;
  is_charging: boolean;
  source_device: string;
}

export default function RoofMonitorScreen({ route }: any) {
  const shootId = route.params?.shootId;
  const token = useAuthStore((s) => s.token);
  const wsRef = useRef<WebSocket | null>(null);
  const [connected, setConnected] = useState(false);
  const [telemetry, setTelemetry] = useState<TelemetryState>({
    signal_strength: 0,
    obstruction_pct: 0,
    tilt_x: 0,
    tilt_y: 0,
    compass_heading: 0,
    latitude: null,
    longitude: null,
    altitude_m: null,
    download_mbps: 0,
    upload_mbps: 0,
    latency_ms: 0,
    phone_battery_pct: 100,
    is_charging: false,
    source_device: Platform.OS === 'ios' ? 'iPhone' : 'Android',
  });

  // Keep screen awake in kiosk mode
  useEffect(() => {
    activateKeepAwakeAsync('roof-monitor');
    return () => { deactivateKeepAwake('roof-monitor'); };
  }, []);

  // Sensors
  useEffect(() => {
    Accelerometer.setUpdateInterval(500);
    const accelSub = Accelerometer.addListener(({ x, y }) => {
      setTelemetry((prev) => ({
        ...prev,
        tilt_x: Math.round(x * 90 * 10) / 10,
        tilt_y: Math.round(y * 90 * 10) / 10,
      }));
    });

    Magnetometer.setUpdateInterval(1000);
    const magSub = Magnetometer.addListener(({ x, y }) => {
      const heading = Math.atan2(y, x) * (180 / Math.PI);
      setTelemetry((prev) => ({
        ...prev,
        compass_heading: heading < 0 ? heading + 360 : heading,
      }));
    });

    return () => { accelSub.remove(); magSub.remove(); };
  }, []);

  // GPS
  useEffect(() => {
    let sub: Location.LocationSubscription | null = null;
    (async () => {
      const { status } = await Location.requestForegroundPermissionsAsync();
      if (status !== 'granted') return;
      sub = await Location.watchPositionAsync(
        { accuracy: Location.Accuracy.High, timeInterval: 5000 },
        (loc) => {
          setTelemetry((prev) => ({
            ...prev,
            latitude: loc.coords.latitude,
            longitude: loc.coords.longitude,
            altitude_m: loc.coords.altitude,
          }));
        }
      );
    })();
    return () => { sub?.remove(); };
  }, []);

  // Battery
  useEffect(() => {
    const interval = setInterval(async () => {
      const level = await Battery.getBatteryLevelAsync();
      const state = await Battery.getBatteryStateAsync();
      setTelemetry((prev) => ({
        ...prev,
        phone_battery_pct: Math.round(level * 100),
        is_charging: state === Battery.BatteryState.CHARGING,
      }));
    }, 10000);
    return () => clearInterval(interval);
  }, []);

  // WebSocket publisher
  useEffect(() => {
    if (!shootId || !token) return;

    const connect = () => {
      const ws = new WebSocket(`${WS_BASE_URL}/ws/roof/${shootId}?token=${token}&role=publisher`);
      ws.onopen = () => setConnected(true);
      ws.onclose = () => {
        setConnected(false);
        setTimeout(connect, 3000); // auto-reconnect
      };
      wsRef.current = ws;
    };
    connect();

    return () => { wsRef.current?.close(); };
  }, [shootId, token]);

  // Emit telemetry every 2s
  useEffect(() => {
    const interval = setInterval(() => {
      if (wsRef.current?.readyState === WebSocket.OPEN) {
        wsRef.current.send(JSON.stringify(telemetry));
      }
    }, 2000);
    return () => clearInterval(interval);
  }, [telemetry]);

  return (
    <View style={styles.container}>
      <Surface style={styles.header} elevation={2}>
        <Icon source={connected ? 'access-point' : 'access-point-off'} size={32}
              color={connected ? '#38A169' : '#E53E3E'} />
        <Text variant="headlineSmall" style={styles.title}>
          📡 Roof Monitor {connected ? '(LIVE)' : '(OFFLINE)'}
        </Text>
      </Surface>

      <View style={styles.grid}>
        <MetricCard label="Signal" value={`${telemetry.signal_strength}%`} icon="signal" />
        <MetricCard label="Obstruction" value={`${(telemetry.obstruction_pct * 100).toFixed(1)}%`} icon="weather-cloudy" />
        <MetricCard label="Tilt X" value={`${telemetry.tilt_x}°`} icon="rotate-left" />
        <MetricCard label="Tilt Y" value={`${telemetry.tilt_y}°`} icon="rotate-right" />
        <MetricCard label="Heading" value={`${Math.round(telemetry.compass_heading)}°`} icon="compass" />
        <MetricCard label="Battery" value={`${telemetry.phone_battery_pct}%`}
                    icon={telemetry.is_charging ? 'battery-charging' : 'battery'} />
      </View>

      <Surface style={styles.footer} elevation={1}>
        <Text variant="bodySmall" style={{ color: '#A0AEC0' }}>
          {telemetry.latitude?.toFixed(5)}, {telemetry.longitude?.toFixed(5)} · Alt {telemetry.altitude_m?.toFixed(0)}m
        </Text>
        <Text variant="bodySmall" style={{ color: '#A0AEC0' }}>
          ↓ {telemetry.download_mbps} Mbps · ↑ {telemetry.upload_mbps} Mbps · {telemetry.latency_ms}ms
        </Text>
      </Surface>
    </View>
  );
}

function MetricCard({ label, value, icon }: { label: string; value: string; icon: string }) {
  return (
    <Surface style={styles.card} elevation={1}>
      <Icon source={icon} size={24} color="#63B3ED" />
      <Text variant="titleLarge" style={styles.cardValue}>{value}</Text>
      <Text variant="bodySmall" style={styles.cardLabel}>{label}</Text>
    </Surface>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#0A0E1A', padding: 16 },
  header: { flexDirection: 'row', alignItems: 'center', gap: 12, padding: 16,
            borderRadius: 12, backgroundColor: '#1A202C', marginBottom: 16 },
  title: { color: '#E2E8F0' },
  grid: { flexDirection: 'row', flexWrap: 'wrap', gap: 12, flex: 1 },
  card: { width: '47%', padding: 16, borderRadius: 12, backgroundColor: '#1A202C',
          alignItems: 'center', gap: 8 },
  cardValue: { color: '#FFFFFF', fontFamily: Platform.OS === 'ios' ? 'Menlo' : 'monospace' },
  cardLabel: { color: '#A0AEC0' },
  footer: { padding: 12, borderRadius: 8, backgroundColor: '#1A202C',
            marginTop: 12, alignItems: 'center', gap: 4 },
});
