import React from 'react';
import { ScrollView, View, StyleSheet } from 'react-native';
import { Card, Text, useTheme } from 'react-native-paper';
import { useTranslation } from 'react-i18next';
import { StatusBadge } from '../../components/StatusBadge';
import { SpeedGauge } from '../../components/SpeedGauge';
import { SourceIndicator } from '../../components/SourceIndicator';

export function AdminDashboardScreen() {
  const { t } = useTranslation();
  const theme = useTheme();
  const shoots = [
    { id: '1', name: 'Série XYZ', ssid: 'WFC-SerieXYZ', devices: 18, isOnline: true, isFailover: false, dl: 165, ul: 32, source: 'starlink' as const },
    { id: '2', name: 'Pub Nike', ssid: 'WFC-PubNike', devices: 7, isOnline: true, isFailover: true, dl: 45, ul: 12, source: '5g' as const },
  ];

  return (
    <ScrollView style={{ flex: 1, backgroundColor: theme.colors.background }} contentContainerStyle={{ padding: 16, gap: 12, paddingBottom: 32 }}>
      <Text style={{ fontSize: 24, fontWeight: '700', color: theme.colors.onSurface }}>{t('admin.dashboard')}</Text>
      <View style={{ flexDirection: 'row', gap: 8 }}>
        <Card style={{ flex: 1, backgroundColor: '#10B98120' }}><Card.Content style={{ alignItems: 'center', paddingVertical: 8 }}><Text style={{ fontSize: 28, fontWeight: '700', color: '#10B981' }}>2</Text><Text style={{ color: theme.colors.onSurfaceVariant, fontSize: 12 }}>Tournages actifs</Text></Card.Content></Card>
        <Card style={{ flex: 1, backgroundColor: '#3B82F620' }}><Card.Content style={{ alignItems: 'center', paddingVertical: 8 }}><Text style={{ fontSize: 28, fontWeight: '700', color: '#3B82F6' }}>25</Text><Text style={{ color: theme.colors.onSurfaceVariant, fontSize: 12 }}>{t('dashboard.devices')}</Text></Card.Content></Card>
        <Card style={{ flex: 1, backgroundColor: '#F59E0B20' }}><Card.Content style={{ alignItems: 'center', paddingVertical: 8 }}><Text style={{ fontSize: 28, fontWeight: '700', color: '#F59E0B' }}>1</Text><Text style={{ color: theme.colors.onSurfaceVariant, fontSize: 12 }}>{t('admin.alerts')}</Text></Card.Content></Card>
      </View>
      {shoots.map((s) => (
        <Card key={s.id} style={{ elevation: 1 }}><Card.Content>
          <View style={{ flexDirection: 'row', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 8 }}>
            <View><Text style={{ fontSize: 18, fontWeight: '600', color: theme.colors.onSurface }}>{s.name}</Text><Text style={{ color: theme.colors.onSurfaceVariant, fontSize: 12 }}>{s.ssid} — {s.devices} appareils</Text></View>
            <StatusBadge isOnline={s.isOnline} isFailover={s.isFailover} />
          </View>
          <SpeedGauge downloadMbps={s.dl} uploadMbps={s.ul} />
          <SourceIndicator source={s.source} isFailover={s.isFailover} />
        </Card.Content></Card>
      ))}
    </ScrollView>
  );
}
