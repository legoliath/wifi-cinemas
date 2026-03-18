import { MD3LightTheme, MD3DarkTheme } from 'react-native-paper';
export const lightTheme = { ...MD3LightTheme, colors: { ...MD3LightTheme.colors, primary: '#1A365D', primaryContainer: '#E8EDF4', secondary: '#4A6FA5', surface: '#FFFFFF', background: '#F8F9FB', error: '#DC2626', onSurface: '#111827', onSurfaceVariant: '#6B7280', outline: '#D1D5DB' }, roundness: 12 };
export const darkTheme = { ...MD3DarkTheme, colors: { ...MD3DarkTheme.colors, primary: '#7BA3D4', primaryContainer: '#1A365D', surface: '#1F2937', background: '#111827', onSurface: '#F9FAFB', onSurfaceVariant: '#9CA3AF' }, roundness: 12 };
export const colors = { starlink: '#00B4D8', cellular: '#F59E0B', online: '#10B981', degraded: '#F59E0B', offline: '#EF4444', failover: '#F97316' };
