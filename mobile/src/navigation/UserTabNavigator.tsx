import React from 'react';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { useTheme } from 'react-native-paper';
import { useTranslation } from 'react-i18next';
import { DashboardScreen } from '../screens/user/DashboardScreen';
import { SupportScreen } from '../screens/user/SupportScreen';
import { SettingsScreen } from '../screens/user/SettingsScreen';

const Tab = createBottomTabNavigator();

export function UserTabNavigator() {
  const theme = useTheme();
  const { t } = useTranslation();
  return (
    <Tab.Navigator screenOptions={{ tabBarActiveTintColor: theme.colors.primary, headerStyle: { backgroundColor: theme.colors.surface }, headerTintColor: theme.colors.onSurface }}>
      <Tab.Screen name="Dashboard" component={DashboardScreen} options={{ title: t('dashboard.title') }} />
      <Tab.Screen name="Support" component={SupportScreen} options={{ title: t('support.title') }} />
      <Tab.Screen name="Settings" component={SettingsScreen} options={{ title: t('settings.title') }} />
    </Tab.Navigator>
  );
}
