import React from 'react';
import { ScrollView, View, StyleSheet } from 'react-native';
import { List, Switch, Button, Divider, useTheme } from 'react-native-paper';
import { useTranslation } from 'react-i18next';
import { useAuthStore } from '../../store/authStore';
import { APP_VERSION } from '../../utils/constants';

export function SettingsScreen() {
  const { t, i18n } = useTranslation();
  const theme = useTheme();
  const user = useAuthStore((s) => s.user);
  const logout = useAuthStore((s) => s.logout);
  const [notifs, setNotifs] = React.useState(true);

  return (
    <ScrollView style={{ flex: 1, backgroundColor: theme.colors.background }}>
      {user && <List.Section><List.Subheader>Profil</List.Subheader><List.Item title={user.name} description={user.email} left={(p) => <List.Icon {...p} icon="account" />} /></List.Section>}
      <Divider />
      <List.Section>
        <List.Subheader>{t('settings.title')}</List.Subheader>
        <List.Item title={t('settings.language')} description={i18n.language === 'fr' ? 'Français' : 'English'} left={(p) => <List.Icon {...p} icon="translate" />} onPress={() => i18n.changeLanguage(i18n.language === 'fr' ? 'en' : 'fr')} />
        <List.Item title={t('settings.notifications')} left={(p) => <List.Icon {...p} icon="bell" />} right={() => <Switch value={notifs} onValueChange={setNotifs} />} />
      </List.Section>
      <Divider />
      <List.Section><List.Item title={t('settings.about')} description={`${t('settings.version')} ${APP_VERSION}`} left={(p) => <List.Icon {...p} icon="information" />} /></List.Section>
      <View style={{ padding: 24 }}><Button mode="outlined" onPress={logout} textColor="#DC2626" icon="logout">{t('auth.logout')}</Button></View>
    </ScrollView>
  );
}
