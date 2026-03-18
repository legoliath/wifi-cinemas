import React from 'react';
import { View, StyleSheet } from 'react-native';
import { Text, useTheme } from 'react-native-paper';
import { useTranslation } from 'react-i18next';
import { formatSpeed } from '../utils/helpers';

export function SpeedGauge({ downloadMbps, uploadMbps }: { downloadMbps: number; uploadMbps: number }) {
  const { t } = useTranslation();
  const theme = useTheme();
  return (
    <View style={styles.container}>
      <View style={styles.item}>
        <Text style={[styles.value, { color: theme.colors.onSurface }]}>{formatSpeed(downloadMbps)}</Text>
        <Text style={{ color: theme.colors.onSurfaceVariant, fontSize: 12 }}>↓ {t('dashboard.download')}</Text>
      </View>
      <View style={[styles.divider, { backgroundColor: theme.colors.outline }]} />
      <View style={styles.item}>
        <Text style={[styles.value, { color: theme.colors.onSurface }]}>{formatSpeed(uploadMbps)}</Text>
        <Text style={{ color: theme.colors.onSurfaceVariant, fontSize: 12 }}>↑ {t('dashboard.upload')}</Text>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flexDirection: 'row', alignItems: 'center', justifyContent: 'center', paddingVertical: 16 },
  item: { flex: 1, alignItems: 'center' },
  value: { fontSize: 22, fontWeight: '700' },
  divider: { width: 1, height: 40, marginHorizontal: 16 },
});
