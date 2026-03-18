import React from 'react';
import { ScrollView } from 'react-native';
import { Card, Text, DataTable, useTheme } from 'react-native-paper';
import { useTranslation } from 'react-i18next';

export function MonitoringScreen() {
  const { t } = useTranslation();
  const theme = useTheme();
  const aps = [{name:'AP-Roulotte-1',clients:8,ch:36},{name:'AP-Roulotte-2',clients:5,ch:149},{name:'AP-Extérieur',clients:1,ch:44}];
  const devices = [{mac:'CC:01',host:'iPhone-Director',ap:'AP-Roulotte-1',sig:-42},{mac:'CC:02',host:'MacBook-Edit',ap:'AP-Roulotte-1',sig:-55},{mac:'CC:03',host:'iPad-Script',ap:'AP-Roulotte-2',sig:-48}];

  return (
    <ScrollView style={{ flex: 1, backgroundColor: theme.colors.background }} contentContainerStyle={{ padding: 16, gap: 12, paddingBottom: 32 }}>
      <Card style={{ elevation: 1 }}><Card.Content>
        <Text style={{ fontSize: 18, fontWeight: '600', marginBottom: 8, color: theme.colors.onSurface }}>Access Points</Text>
        <DataTable>
          <DataTable.Header><DataTable.Title>AP</DataTable.Title><DataTable.Title numeric>Clients</DataTable.Title><DataTable.Title numeric>Canal</DataTable.Title></DataTable.Header>
          {aps.map(a => <DataTable.Row key={a.name}><DataTable.Cell>{a.name}</DataTable.Cell><DataTable.Cell numeric>{a.clients}</DataTable.Cell><DataTable.Cell numeric>{a.ch}</DataTable.Cell></DataTable.Row>)}
        </DataTable>
      </Card.Content></Card>
      <Card style={{ elevation: 1 }}><Card.Content>
        <Text style={{ fontSize: 18, fontWeight: '600', marginBottom: 8, color: theme.colors.onSurface }}>{t('dashboard.devices')} ({devices.length})</Text>
        <DataTable>
          <DataTable.Header><DataTable.Title>Appareil</DataTable.Title><DataTable.Title>AP</DataTable.Title><DataTable.Title numeric>Signal</DataTable.Title></DataTable.Header>
          {devices.map(d => <DataTable.Row key={d.mac}><DataTable.Cell>{d.host}</DataTable.Cell><DataTable.Cell>{d.ap}</DataTable.Cell><DataTable.Cell numeric>{d.sig} dBm</DataTable.Cell></DataTable.Row>)}
        </DataTable>
      </Card.Content></Card>
    </ScrollView>
  );
}
