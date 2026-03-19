"""UniFi Controller API Client — manages APs, SSIDs, client tracking.

Uses direct REST API calls (no external dependency).
Handles both UniFi OS (port 443) and legacy controller (port 8443).
"""
import logging
from typing import Optional
import httpx
from app.config import settings

logger = logging.getLogger(__name__)


class UniFiClient:
    def __init__(self):
        self.base_url = settings.unifi_controller_url.rstrip("/")
        self.username = settings.unifi_username
        self.password = settings.unifi_password
        self.site = settings.unifi_site
        self._cookies: Optional[dict] = None
        self._csrf: Optional[str] = None

    async def _ensure_session(self, client: httpx.AsyncClient):
        """Login and store session cookies + CSRF token."""
        if self._cookies:
            return

        # Try UniFi OS auth first (UDM, Cloud Key Gen2+)
        try:
            r = await client.post(
                f"{self.base_url}/api/auth/login",
                json={"username": self.username, "password": self.password},
                timeout=10,
            )
            if r.status_code == 200:
                self._cookies = dict(r.cookies)
                self._csrf = r.headers.get("x-csrf-token")
                logger.info("UniFi OS login successful")
                return
        except Exception:
            pass

        # Fallback: legacy controller
        try:
            r = await client.post(
                f"{self.base_url}/api/login",
                json={"username": self.username, "password": self.password},
                timeout=10,
            )
            if r.status_code == 200:
                self._cookies = dict(r.cookies)
                logger.info("UniFi legacy login successful")
                return
        except Exception as e:
            logger.warning(f"UniFi login failed: {e}")

    def _headers(self) -> dict:
        headers = {}
        if self._csrf:
            headers["x-csrf-token"] = self._csrf
        return headers

    async def get_clients(self) -> list[dict]:
        """Get all connected wireless clients (stations)."""
        try:
            async with httpx.AsyncClient(verify=False) as client:
                await self._ensure_session(client)
                if not self._cookies:
                    return self._mock_clients()

                r = await client.get(
                    f"{self.base_url}/proxy/network/api/s/{self.site}/stat/sta",
                    cookies=self._cookies,
                    headers=self._headers(),
                    timeout=10,
                )
                if r.status_code != 200:
                    # Try legacy path
                    r = await client.get(
                        f"{self.base_url}/api/s/{self.site}/stat/sta",
                        cookies=self._cookies,
                        headers=self._headers(),
                        timeout=10,
                    )

                if r.status_code == 200:
                    data = r.json().get("data", [])
                    return [
                        {
                            "mac": c.get("mac", ""),
                            "hostname": c.get("hostname") or c.get("name", "Unknown"),
                            "ip": c.get("ip", ""),
                            "ap_name": c.get("ap_name", ""),
                            "ssid": c.get("essid", ""),
                            "signal": c.get("signal", 0),
                            "rx_bytes": c.get("rx_bytes", 0),
                            "tx_bytes": c.get("tx_bytes", 0),
                            "uptime": c.get("uptime", 0),
                            "authorized": c.get("authorized", False),
                        }
                        for c in data
                        if not c.get("is_wired", False)
                    ]
                logger.warning(f"UniFi get_clients failed: {r.status_code}")
                return self._mock_clients()
        except Exception as e:
            logger.warning(f"UniFi get_clients error: {e}")
            return self._mock_clients()

    async def get_access_points(self) -> list[dict]:
        """Get all access points and their status."""
        try:
            async with httpx.AsyncClient(verify=False) as client:
                await self._ensure_session(client)
                if not self._cookies:
                    return self._mock_aps()

                r = await client.get(
                    f"{self.base_url}/proxy/network/api/s/{self.site}/stat/device",
                    cookies=self._cookies,
                    headers=self._headers(),
                    timeout=10,
                )
                if r.status_code != 200:
                    r = await client.get(
                        f"{self.base_url}/api/s/{self.site}/stat/device",
                        cookies=self._cookies,
                        headers=self._headers(),
                        timeout=10,
                    )

                if r.status_code == 200:
                    data = r.json().get("data", [])
                    return [
                        {
                            "name": d.get("name", d.get("mac", "Unknown")),
                            "mac": d.get("mac", ""),
                            "model": d.get("model", ""),
                            "status": "connected" if d.get("state", 0) == 1 else "disconnected",
                            "clients": d.get("num_sta", 0),
                            "uptime": d.get("uptime", 0),
                            "channel_2g": d.get("radio_table_stats", [{}])[0].get("channel") if d.get("radio_table_stats") else None,
                            "channel_5g": d.get("radio_table_stats", [{}])[-1].get("channel") if len(d.get("radio_table_stats", [])) > 1 else None,
                        }
                        for d in data
                        if d.get("type") in ("uap", "udm")
                    ]
                return self._mock_aps()
        except Exception as e:
            logger.warning(f"UniFi get_access_points error: {e}")
            return self._mock_aps()

    async def set_ssid(self, ssid: str, passphrase: str) -> bool:
        """Update SSID name and passphrase on the controller."""
        try:
            async with httpx.AsyncClient(verify=False) as client:
                await self._ensure_session(client)
                if not self._cookies:
                    return False

                # Get current WLAN config
                r = await client.get(
                    f"{self.base_url}/proxy/network/api/s/{self.site}/rest/wlanconf",
                    cookies=self._cookies,
                    headers=self._headers(),
                    timeout=10,
                )
                if r.status_code != 200:
                    r = await client.get(
                        f"{self.base_url}/api/s/{self.site}/rest/wlanconf",
                        cookies=self._cookies,
                        headers=self._headers(),
                        timeout=10,
                    )

                if r.status_code != 200:
                    return False

                wlans = r.json().get("data", [])
                # Find the crew SSID (not the admin one)
                target = next((w for w in wlans if not w.get("name", "").startswith("WFC-Admin")), None)
                if not target:
                    logger.warning("No crew SSID found to update")
                    return False

                wlan_id = target["_id"]
                update_url = f"{self.base_url}/proxy/network/api/s/{self.site}/rest/wlanconf/{wlan_id}"
                r = await client.put(
                    update_url,
                    json={"name": ssid, "x_passphrase": passphrase},
                    cookies=self._cookies,
                    headers=self._headers(),
                    timeout=10,
                )
                return r.status_code == 200
        except Exception as e:
            logger.error(f"UniFi set_ssid error: {e}")
            return False

    async def block_client(self, mac: str) -> bool:
        """Block a client by MAC address."""
        try:
            async with httpx.AsyncClient(verify=False) as client:
                await self._ensure_session(client)
                if not self._cookies:
                    return False

                r = await client.post(
                    f"{self.base_url}/proxy/network/api/s/{self.site}/cmd/stamgr",
                    json={"cmd": "block-sta", "mac": mac},
                    cookies=self._cookies,
                    headers=self._headers(),
                    timeout=10,
                )
                return r.status_code == 200
        except Exception as e:
            logger.error(f"UniFi block_client error: {e}")
            return False

    @staticmethod
    def _mock_clients() -> list[dict]:
        return [
            {"mac": "AA:BB:CC:DD:EE:01", "hostname": "iPhone-Réalisateur", "ip": "192.168.1.101",
             "ap_name": "AP-Roulotte-1", "ssid": "WFC-PlateauMtl", "signal": -55,
             "rx_bytes": 1_500_000_000, "tx_bytes": 200_000_000, "uptime": 14400, "authorized": True},
            {"mac": "AA:BB:CC:DD:EE:02", "hostname": "MacBook-Script", "ip": "192.168.1.102",
             "ap_name": "AP-Roulotte-1", "ssid": "WFC-PlateauMtl", "signal": -62,
             "rx_bytes": 5_000_000_000, "tx_bytes": 800_000_000, "uptime": 28800, "authorized": True},
            {"mac": "AA:BB:CC:DD:EE:03", "hostname": "iPad-DIT", "ip": "192.168.1.103",
             "ap_name": "AP-Plateau-2", "ssid": "WFC-PlateauMtl", "signal": -70,
             "rx_bytes": 800_000_000, "tx_bytes": 50_000_000, "uptime": 7200, "authorized": True},
        ]

    @staticmethod
    def _mock_aps() -> list[dict]:
        return [
            {"name": "AP-Roulotte-1", "mac": "00:11:22:33:44:01", "model": "U6-Pro",
             "status": "connected", "clients": 8, "uptime": 86400, "channel_2g": 6, "channel_5g": 36},
            {"name": "AP-Plateau-2", "mac": "00:11:22:33:44:02", "model": "U6-Mesh",
             "status": "connected", "clients": 5, "uptime": 86400, "channel_2g": 11, "channel_5g": 149},
        ]


unifi_client = UniFiClient()
