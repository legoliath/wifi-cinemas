import React from 'react';
import { NavigationContainer } from '@react-navigation/native';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { useTheme } from 'react-native-paper';
import { useAuthStore } from '../store/authStore';
import { LoginScreen } from '../screens/auth/LoginScreen';
import { QRScanScreen } from '../screens/auth/QRScanScreen';
import { OnboardingScreen } from '../screens/auth/OnboardingScreen';
import { UserTabNavigator } from './UserTabNavigator';
import { AdminTabNavigator } from './AdminTabNavigator';

const Stack = createNativeStackNavigator();

export function AppNavigator() {
  const theme = useTheme();
  const isAuth = useAuthStore((s) => s.isAuthenticated);
  const user = useAuthStore((s) => s.user);

  return (
    <NavigationContainer>
      <Stack.Navigator screenOptions={{ headerStyle: { backgroundColor: theme.colors.surface }, headerTintColor: theme.colors.onSurface, headerShadowVisible: false }}>
        {!isAuth ? (
          <>
            <Stack.Screen name="Login" component={LoginScreen} options={{ headerShown: false }} />
            <Stack.Screen name="QRScan" component={QRScanScreen} options={{ title: 'Scanner QR' }} />
            <Stack.Screen name="Onboarding" component={OnboardingScreen} options={{ title: 'Inscription' }} />
          </>
        ) : user?.role === 'admin' ? (
          <Stack.Screen name="AdminTabs" component={AdminTabNavigator} options={{ headerShown: false }} />
        ) : (
          <Stack.Screen name="UserTabs" component={UserTabNavigator} options={{ headerShown: false }} />
        )}
      </Stack.Navigator>
    </NavigationContainer>
  );
}
