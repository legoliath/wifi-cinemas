/**
 * WiFi Auto-Configuration — requires expo prebuild (bare workflow).
 * iOS: NEHotspotConfiguration, Android: WifiManager
 */
export async function configureWifi(ssid: string, passphrase: string): Promise<boolean> {
  console.warn(`[WiFi Config] Would connect to: ${ssid} — native module required`);
  return false;
}

export async function removeWifiConfig(ssid: string): Promise<boolean> {
  console.warn(`[WiFi Config] Would remove: ${ssid}`);
  return false;
}
