import React from 'react';
import { View, FlatList, StyleSheet } from 'react-native';
import { Card, Text, Button, Chip, FAB, useTheme } from 'react-native-paper';
import { useTranslation } from 'react-i18next';

const SHOOTS = [
  { id: '1', name: 'Série XYZ', client: 'Productions ABC', ssid: 'WFC-SerieXYZ', status: 'active', startDate: '2026-03-10' },
  { id: '2', name: 'Pub Nike', client: 'Agence Créative', ssid: 'WFC-PubNike', status: 'active', startDate: '2026-03-18' },
  { id: '3', name: 'Film Été 2026', client: 'Studio Lumière', ssid: 'WFC-FilmEte2026', status: 'scheduled', startDate: '2026-06-01' },
];

const STATUS_COLORS: Record<string,string> = { active: '#10B981', scheduled: '#3B82F6', completed: '#6B7280' };

export function ShootManagementScreen() {
  const { t } = useTranslation();
  const theme = useTheme();
  return (
    <View style={{ flex: 1, backgroundColor: theme.colors.background }}>
      <FlatList data={SHOOTS} contentContainerStyle={{ padding: 16, gap: 12, paddingBottom: 100 }} keyExtractor={(i) => i.id} renderItem={({ item }) => (
        <Card style={{ elevation: 1 }}><Card.Content>
          <View style={{ flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 4 }}>
            <Text style={{ fontSize: 18, fontWeight: '600', color: theme.colors.onSurface }}>{item.name}</Text>
            <Chip compact textStyle={{ fontSize: 11, color: STATUS_COLORS[item.status] }} style={{ backgroundColor: (STATUS_COLORS[item.status]||'#999') + '20' }}>{item.status}</Chip>
          </View>
          <Text style={{ color: theme.colors.onSurfaceVariant }}>{item.client}</Text>
          <Text style={{ color: theme.colors.onSurfaceVariant, fontSize: 12 }}>{item.ssid} · {item.startDate}</Text>
        </Card.Content><Card.Actions><Button compact>{t('admin.generateCodes')}</Button></Card.Actions></Card>
      )} />
      <FAB icon="plus" label={t('admin.createShoot')} style={{ position: 'absolute', right: 16, bottom: 24, backgroundColor: theme.colors.primary }} color="#fff" onPress={() => {}} />
    </View>
  );
}
