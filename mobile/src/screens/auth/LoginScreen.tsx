import React, { useState } from 'react';
import { View, StyleSheet, KeyboardAvoidingView, Platform } from 'react-native';
import { TextInput, Button, Text, useTheme } from 'react-native-paper';
import { useTranslation } from 'react-i18next';
import { useAuthStore } from '../../store/authStore';
import { loginWithEmail } from '../../services/firebase';

export function LoginScreen({ navigation }: any) {
  const { t } = useTranslation();
  const theme = useTheme();
  const setAuth = useAuthStore((s) => s.setAuth);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleLogin = async () => {
    setLoading(true); setError('');
    try {
      const r = await loginWithEmail(email, password);
      setAuth(r.accessToken, { id: r.userId, email, name: email.split('@')[0], role: r.role as any, lang: 'fr', isActive: true, createdAt: new Date().toISOString() });
    } catch (e: any) { setError(e.response?.data?.detail || 'Erreur'); }
    finally { setLoading(false); }
  };

  return (
    <KeyboardAvoidingView style={[styles.container, { backgroundColor: theme.colors.background }]} behavior={Platform.OS === 'ios' ? 'padding' : 'height'}>
      <View style={styles.header}>
        <Text style={[styles.title, { color: theme.colors.primary }]}>📡 WiFi Cinémas</Text>
        <Text style={{ color: theme.colors.onSurfaceVariant, textAlign: 'center' }}>Internet professionnel pour vos tournages</Text>
      </View>
      <View style={styles.form}>
        <TextInput label={t('auth.email')} value={email} onChangeText={setEmail} keyboardType="email-address" autoCapitalize="none" mode="outlined" />
        <TextInput label={t('auth.password')} value={password} onChangeText={setPassword} secureTextEntry mode="outlined" />
        {error ? <Text style={{ color: '#DC2626', textAlign: 'center' }}>{error}</Text> : null}
        <Button mode="contained" onPress={handleLogin} loading={loading} disabled={!email || !password}>{t('auth.login')}</Button>
        <Button mode="outlined" onPress={() => navigation.navigate('QRScan')} icon="qrcode-scan">{t('auth.scanQR')}</Button>
        <Button mode="text" onPress={() => navigation.navigate('Onboarding')}>{t('auth.enterCode')}</Button>
      </View>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, justifyContent: 'center', padding: 24 },
  header: { alignItems: 'center', marginBottom: 40 },
  title: { fontSize: 28, fontWeight: '700', marginBottom: 8 },
  form: { gap: 12 },
});
