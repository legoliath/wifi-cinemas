import React from 'react';
import { View, StyleSheet } from 'react-native';
import { Text, Button, useTheme } from 'react-native-paper';
import { useTranslation } from 'react-i18next';

export function QRScanScreen({ navigation }: any) {
  const { t } = useTranslation();
  const theme = useTheme();
  return (
    <View style={[styles.container, { backgroundColor: theme.colors.background }]}>
      <View style={styles.camera}>
        <Text style={{ color: '#fff', fontSize: 48 }}>📷</Text>
        <Text style={{ color: '#fff', textAlign: 'center', marginTop: 12 }}>{t('auth.scanInstructions')}</Text>
        <Text style={{ color: '#999', fontSize: 12, marginTop: 8 }}>Camera requires expo prebuild</Text>
      </View>
      <View style={{ padding: 24 }}>
        <Button mode="outlined" onPress={() => navigation.navigate('Onboarding')} icon="keyboard">{t('auth.enterCode')}</Button>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1 },
  camera: { flex: 1, justifyContent: 'center', alignItems: 'center', backgroundColor: '#000', margin: 24, borderRadius: 16 },
});
