import React, { useState } from 'react';
import { ScrollView, Alert, StyleSheet } from 'react-native';
import { TextInput, Button, Card, Text, useTheme } from 'react-native-paper';
import { useTranslation } from 'react-i18next';

export function SupportScreen() {
  const { t } = useTranslation();
  const theme = useTheme();
  const [desc, setDesc] = useState('');

  return (
    <ScrollView style={[styles.c, { backgroundColor: theme.colors.background }]} contentContainerStyle={{ padding: 16, gap: 12 }}>
      <Card><Card.Content>
        <Text style={{ fontSize: 18, fontWeight: '600', marginBottom: 16, color: theme.colors.onSurface }}>{t('support.reportIssue')}</Text>
        <TextInput label={t('support.reportIssue')} value={desc} onChangeText={setDesc} mode="outlined" multiline numberOfLines={5} style={{ marginBottom: 16 }} />
        <Button mode="contained" onPress={() => { setDesc(''); Alert.alert('✅', t('support.sent')); }} disabled={!desc} icon="send">{t('support.reportIssue')}</Button>
      </Card.Content></Card>
      <Card><Card.Content><Button mode="outlined" icon="phone">{t('support.contactOperator')}</Button></Card.Content></Card>
    </ScrollView>
  );
}
const styles = StyleSheet.create({ c: { flex: 1 } });
