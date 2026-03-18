import React from 'react';
import { ScrollView, View, StyleSheet } from 'react-native';
import { Card, Text, useTheme } from 'react-native-paper';
import { useTranslation } from 'react-i18next';
import { StatusBadge } from '../../components/StatusBadge';
import { SpeedGauge } from '../../components/SpeedGauge';
import { SourceIndicator } from '../../components/SourceIndicator';
import { useNetworkStore } from '../../store/networkStore';
import { formatLatency, formatPacketLoss } from '../../utils/helpers';

export function DashboardScreen() {
  const { t } = useTranslation();
  const theme = useTheme();
  const status = useNetworkStore((s) => s.status);
  const mock = status || { isOnline: true, isFailover: false, source: 'starlink' as const, downloadMbps: 152.3, uploadMbps: 28.7, latencyMs: 32, packetLoss: 0.1, connectedDevices: 14 };

  return (
    <ScrollView style={[styles.container, { backgroundColor: theme.colors.background }]} contentContainerStyle={styles.content}>
      <Card style={styles.card}><Card.Content>
        <View style={{ flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' }}>
          <Text style={{ fontSize: 16, fontWeight: '600', color: theme.colors.onSurface }}>{t('dashboard.connectionStatus')}</Text>
          <StatusBadge isOnline={mock.isOnline} isFailover={mock.isFailover} />
        </View>
      </Card.Content></Card>
      <Card style={styles.card}><Card.Content><SpeedGauge downloadMbps={mock.downloadMbps} uploadMbps={mock.uploadMbps} /></Card.Content></Card>
      <Card style={styles.card}><Card.Content><SourceIndicator source={mock.source} isFailover={mock.isFailover} /></Card.Content></Card>
      <Card style={styles.card}><Card.Content>
        <Text style={{ fontSize: 16, fontWeight: '600', color: theme.colors.onSurface, marginBottom: 12 }}>{t('dashboard.networkHealth')}</Text>
        <View style={{ flexDirection: 'row', justifyContent: 'space-around' }}>
          <View style={{ alignItems: 'center' }}><Text style={{ fontSize: 20, fontWeight: '700', color: theme.colors.primary }}>{formatLatency(mock.latencyMs)}</Text><Text style={{ fontSize: 12, color: theme.colors.onSurfaceVariant }}>{t('dashboard.latency')}</Text></View>
          <View style={{ alignItems: 'center' }}><Text style={{ fontSize: 20, fontWeight: '700', color: theme.colors.primary }}>{formatPacketLoss(mock.packetLoss)}</Text><Text style={{ fontSize: 12, color: theme.colors.onSurfaceVariant }}>{t('dashboard.packetLoss')}</Text></View>
          <View style={{ alignItems: 'center' }}><Text style={{ fontSize: 20, fontWeight: '700', color: theme.colors.primary }}>{mock.connectedDevices}</Text><Text style={{ fontSize: 12, color: theme.colors.onSurfaceVariant }}>{t('dashboard.devices')}</Text></View>
        </View>
      </Card.Content></Card>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1 },
  content: { padding: 16, gap: 12, paddingBottom: 32 },
  card: { elevation: 1 },
});
