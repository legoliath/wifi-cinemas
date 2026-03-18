import React from 'react';
import { View, StyleSheet } from 'react-native';
import { Text, useTheme } from 'react-native-paper';
import { useTranslation } from 'react-i18next';
import { colors } from '../theme';
import type { NetworkSource } from '../types';

export function SourceIndicator({ source, isFailover }: { source: NetworkSource; isFailover: boolean }) {
  const { t } = useTranslation();
  const theme = useTheme();
  const color = source === 'starlink' ? colors.starlink : colors.cellular;
  const icon = source === 'starlink' ? '🛰️' : '📡';
  const label = source === 'starlink' ? t('dashboard.starlink') : t('dashboard.cellular');
  return (
    <View style={[styles.container, { backgroundColor: color + '15' }]}>
      <Text style={{ fontSize: 28 }}>{icon}</Text>
      <View>
        <Text style={{ color, fontSize: 16, fontWeight: '700' }}>{label}</Text>
        <Text style={{ color: theme.colors.onSurfaceVariant, fontSize: 12 }}>{t('dashboard.source')}{isFailover ? ` — ${t('dashboard.failover')}` : ''}</Text>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flexDirection: 'row', alignItems: 'center', padding: 12, borderRadius: 12, gap: 12 },
});
