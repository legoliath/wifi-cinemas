import React from 'react';
import { createMaterialBottomTabNavigator } from 'react-native-paper/react-navigation';
import { useTheme } from 'react-native-paper';
import TechDashboardScreen from '../screens/tech/TechDashboardScreen';
import RoofMonitorScreen from '../screens/tech/RoofMonitorScreen';
import { DashboardScreen } from '../screens/user/DashboardScreen';
import { SettingsScreen } from '../screens/user/SettingsScreen';

const Tab = createMaterialBottomTabNavigator();

export function TechTabNavigator() {
  const theme = useTheme();
  return (
    <Tab.Navigator
      barStyle={{ backgroundColor: theme.colors.surface }}
      activeColor={theme.colors.primary}
    >
      <Tab.Screen
        name="TechDashboard"
        component={TechDashboardScreen}
        options={{ tabBarLabel: 'Roof Live', tabBarIcon: 'satellite-uplink' }}
      />
      <Tab.Screen
        name="RoofMonitor"
        component={RoofMonitorScreen}
        options={{ tabBarLabel: 'Mode Toit', tabBarIcon: 'cellphone-link' }}
      />
      <Tab.Screen
        name="Network"
        component={DashboardScreen}
        options={{ tabBarLabel: 'Réseau', tabBarIcon: 'wifi' }}
      />
      <Tab.Screen
        name="Settings"
        component={SettingsScreen}
        options={{ tabBarLabel: 'Paramètres', tabBarIcon: 'cog' }}
      />
    </Tab.Navigator>
  );
}
