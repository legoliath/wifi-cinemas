import React from 'react';
import { View, StyleSheet } from 'react-native';
import { Text } from 'react-native-paper';
import { useTranslation } from 'react-i18next';
import { getConnectionColor } from '../utils/helpers';

export function StatusBadge({ isOnline, isFailover }: { isOnline: boolean; isFailover: boolean }) {
  const { t } = useTranslation();
  const color = getConnectionColor(isOnline, isFailover);
  const label = !isOnline ? t('dashboard.offline') : isFailover ? t('dashboard.failover') : t('dashboard.online');
  return (
    <View style={[styles.badge, { backgroundColor: color + '20', borderColor: color }]}>
      <View style={[styles.dot, { backgroundColor: color }]} />
      <Text style={{ color, fontWeight: '600', fontSize: 12 }}>{label}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  badge: { flexDirection: 'row', alignItems: 'center', paddingHorizontal: 12, paddingVertical: 6, borderRadius: 20, borderWidth: 1, alignSelf: 'flex-start' },
  dot: { width: 8, height: 8, borderRadius: 4, marginRight: 6 },
});
