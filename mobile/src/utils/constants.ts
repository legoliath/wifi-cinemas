export const APP_NAME = 'WiFi Cinémas';
export const APP_VERSION = '0.1.0';
export const QR_PREFIX = 'wfc://';

// API — switch to your server IP/domain in production
export const API_BASE_URL = __DEV__ ? 'http://localhost:8000' : 'https://api.wificinemas.com';
export const WS_BASE_URL = __DEV__ ? 'ws://localhost:8000' : 'wss://api.wificinemas.com';
