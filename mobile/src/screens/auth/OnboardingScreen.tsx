import React, { useState } from 'react';
import { View, StyleSheet, KeyboardAvoidingView, Platform } from 'react-native';
import { TextInput, Button, Text, useTheme } from 'react-native-paper';
import { useTranslation } from 'react-i18next';
import { useAuthStore } from '../../store/authStore';
import { verifyInviteCode, registerWithInviteCode } from '../../services/firebase';

export function OnboardingScreen({ navigation, route }: any) {
  const { t } = useTranslation();
  const theme = useTheme();
  const setAuth = useAuthStore((s) => s.setAuth);
  const initialCode = route.params?.inviteCode || '';
  const [step, setStep] = useState<'code'|'register'>(initialCode ? 'register' : 'code');
  const [code, setCode] = useState(initialCode);
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleVerify = async () => {
    setLoading(true); setError('');
    try { const r = await verifyInviteCode(code); if (r.valid) setStep('register'); }
    catch (e: any) { setError(e.response?.data?.detail || 'Code invalide'); }
    finally { setLoading(false); }
  };

  const handleRegister = async () => {
    setLoading(true); setError('');
    try {
      const r = await registerWithInviteCode(email, name, password, code);
      setAuth(r.accessToken, { id: r.userId, email, name, role: r.role as any, lang: 'fr', isActive: true, createdAt: new Date().toISOString() });
    } catch (e: any) { setError(e.response?.data?.detail || "Erreur d'inscription"); }
    finally { setLoading(false); }
  };

  return (
    <KeyboardAvoidingView style={[styles.container, { backgroundColor: theme.colors.background }]} behavior={Platform.OS === 'ios' ? 'padding' : 'height'}>
      <Text style={[styles.title, { color: theme.colors.primary }]}>{step === 'code' ? "🎟️ Code d'accès" : '👤 Créer votre compte'}</Text>
      {step === 'code' ? (
        <View style={styles.form}>
          <TextInput label={t('auth.inviteCode')} value={code} onChangeText={(v) => setCode(v.toUpperCase())} autoCapitalize="characters" mode="outlined" />
          {error ? <Text style={{ color: '#DC2626', textAlign: 'center' }}>{error}</Text> : null}
          <Button mode="contained" onPress={handleVerify} loading={loading} disabled={!code}>{t('common.confirm')}</Button>
        </View>
      ) : (
        <View style={styles.form}>
          <TextInput label={t('auth.name')} value={name} onChangeText={setName} mode="outlined" />
          <TextInput label={t('auth.email')} value={email} onChangeText={setEmail} keyboardType="email-address" autoCapitalize="none" mode="outlined" />
          <TextInput label={t('auth.password')} value={password} onChangeText={setPassword} secureTextEntry mode="outlined" />
          {error ? <Text style={{ color: '#DC2626', textAlign: 'center' }}>{error}</Text> : null}
          <Button mode="contained" onPress={handleRegister} loading={loading} disabled={!name || !email || !password}>{t('auth.register')}</Button>
        </View>
      )}
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, justifyContent: 'center', padding: 24 },
  title: { fontSize: 22, fontWeight: '700', textAlign: 'center', marginBottom: 24 },
  form: { gap: 12 },
});
