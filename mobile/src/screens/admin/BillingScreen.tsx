import React from 'react';
import { ScrollView } from 'react-native';
import { Card, Text, DataTable, useTheme } from 'react-native-paper';
import { useTranslation } from 'react-i18next';

export function BillingScreen() {
  const { t } = useTranslation();
  const theme = useTheme();
  const entries = [{date:'03-18',shoot:'Série XYZ',h:10,amt:750},{date:'03-17',shoot:'Série XYZ',h:12,amt:900},{date:'03-18',shoot:'Pub Nike',h:8,amt:600}];
  const total = entries.reduce((s,e) => s + e.amt, 0);

  return (
    <ScrollView style={{ flex: 1, backgroundColor: theme.colors.background }} contentContainerStyle={{ padding: 16 }}>
      <Card style={{ elevation: 1 }}><Card.Content>
        <Text style={{ fontSize: 18, fontWeight: '600', marginBottom: 8, color: theme.colors.onSurface }}>{t('admin.billing')}</Text>
        <DataTable>
          <DataTable.Header><DataTable.Title>Date</DataTable.Title><DataTable.Title>Tournage</DataTable.Title><DataTable.Title numeric>Heures</DataTable.Title><DataTable.Title numeric>$</DataTable.Title></DataTable.Header>
          {entries.map((e,i) => <DataTable.Row key={i}><DataTable.Cell>{e.date}</DataTable.Cell><DataTable.Cell>{e.shoot}</DataTable.Cell><DataTable.Cell numeric>{e.h}h</DataTable.Cell><DataTable.Cell numeric>{e.amt}$</DataTable.Cell></DataTable.Row>)}
          <DataTable.Row style={{ backgroundColor: theme.colors.surfaceVariant }}><DataTable.Cell><Text style={{ fontWeight: '700' }}>Total</Text></DataTable.Cell><DataTable.Cell>{''}</DataTable.Cell><DataTable.Cell numeric><Text style={{ fontWeight: '700' }}>{entries.reduce((s,e)=>s+e.h,0)}h</Text></DataTable.Cell><DataTable.Cell numeric><Text style={{ fontWeight: '700' }}>{total}$</Text></DataTable.Cell></DataTable.Row>
        </DataTable>
      </Card.Content></Card>
    </ScrollView>
  );
}
