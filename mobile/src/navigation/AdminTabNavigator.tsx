import React from 'react';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { useTheme } from 'react-native-paper';
import { useTranslation } from 'react-i18next';
import { AdminDashboardScreen } from '../screens/admin/AdminDashboardScreen';
import { ShootManagementScreen } from '../screens/admin/ShootManagementScreen';
import { UserManagementScreen } from '../screens/admin/UserManagementScreen';
import { MonitoringScreen } from '../screens/admin/MonitoringScreen';
import { SettingsScreen } from '../screens/user/SettingsScreen';

const Tab = createBottomTabNavigator();

export function AdminTabNavigator() {
  const theme = useTheme();
  const { t } = useTranslation();
  return (
    <Tab.Navigator screenOptions={{ tabBarActiveTintColor: theme.colors.primary, headerStyle: { backgroundColor: theme.colors.surface }, headerTintColor: theme.colors.onSurface }}>
      <Tab.Screen name="AdminDashboard" component={AdminDashboardScreen} options={{ title: t('admin.dashboard') }} />
      <Tab.Screen name="Shoots" component={ShootManagementScreen} options={{ title: t('admin.shoots') }} />
      <Tab.Screen name="Users" component={UserManagementScreen} options={{ title: t('admin.users') }} />
      <Tab.Screen name="Monitoring" component={MonitoringScreen} options={{ title: t('admin.monitoring') }} />
      <Tab.Screen name="More" component={SettingsScreen} options={{ title: t('admin.more') }} />
    </Tab.Navigator>
  );
}
