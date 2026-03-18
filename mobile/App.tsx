import React from 'react';
import { StatusBar } from 'expo-status-bar';
import { PaperProvider } from 'react-native-paper';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { lightTheme } from './src/theme';
import { AppNavigator } from './src/navigation/AppNavigator';
import './src/i18n';

const queryClient = new QueryClient({ defaultOptions: { queries: { retry: 2, staleTime: 30000 } } });

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <PaperProvider theme={lightTheme}>
        <StatusBar style="dark" />
        <AppNavigator />
      </PaperProvider>
    </QueryClientProvider>
  );
}
