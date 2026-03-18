import React from 'react';
import { FlatList, View } from 'react-native';
import { Card, Text, Button, Chip, useTheme } from 'react-native-paper';

const ALERTS = [
  { id: '1', type: 'failover_active', severity: 'warning', message: 'Pub Nike: basculement vers 5G Telus', ack: false, time: '17:45' },
  { id: '2', type: 'high_latency', severity: 'info', message: 'Série XYZ: latence élevée (85ms)', ack: true, time: '16:30' },
];
const SEV_COLORS: Record<string,string> = { info: '#3B82F6', warning: '#F59E0B', critical: '#EF4444' };

export function AlertsScreen() {
  const theme = useTheme();
  return (
    <FlatList data={ALERTS} style={{ flex: 1, backgroundColor: theme.colors.background }} contentContainerStyle={{ padding: 16, gap: 8 }}
      keyExtractor={(i) => i.id} renderItem={({ item }) => (
        <Card style={{ elevation: 1, borderLeftWidth: 4, borderLeftColor: SEV_COLORS[item.severity] }}><Card.Content>
          <View style={{ flexDirection: 'row', justifyContent: 'space-between', marginBottom: 8 }}>
            <Chip compact textStyle={{ fontSize: 11, color: SEV_COLORS[item.severity] }} style={{ backgroundColor: SEV_COLORS[item.severity] + '20' }}>{item.severity}</Chip>
            {item.ack && <Text style={{ color: '#10B981', fontSize: 12 }}>✓ Acquittée</Text>}
          </View>
          <Text style={{ color: theme.colors.onSurface, marginBottom: 4 }}>{item.message}</Text>
          <Text style={{ color: theme.colors.onSurfaceVariant, fontSize: 12 }}>{item.time}</Text>
        </Card.Content>
        {!item.ack && <Card.Actions><Button compact>Acquitter</Button></Card.Actions>}
        </Card>
    )} />
  );
}
