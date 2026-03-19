"""Peplink InControl2 API — WAN monitoring, failover status, cellular data usage.

Uses OAuth2 client credentials for authentication.
Falls back to mock data if InControl is unreachable.
"""
import logging
import time
from typing import Optional
import httpx
from app.config import settings

logger = logging.getLogger(__name__)


class PeplinkClient:
    def __init__(self):
        self.api_url = settings.peplink_ic2_api_url.rstrip("/")
        self.client_id = settings.peplink_client_id
        self.client_secret = settings.peplink_client_secret
        self._access_token: Optional[str] = None
        self._token_expires: float = 0
        # These would come from config or be discovered
        self._org_id: str = ""
        self._group_id: str = ""
        self._device_id: str = ""

    async def _ensure_token(self, client: httpx.AsyncClient):
        """OAuth2 token acquisition."""
        if self._access_token and time.time() < self._token_expires:
            return

        if not self.client_id or not self.client_secret:
            logger.debug("Peplink credentials not configured")
            return

        try:
            r = await client.post(
                f"{self.api_url}/api/oauth2/token",
                data={
                    "grant_type": "client_credentials",
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                },
                timeout=10,
            )
            if r.status_code == 200:
                data = r.json()
                self._access_token = data["access_token"]
                self._token_expires = time.time() + data.get("expires_in", 172800) - 60
                logger.info("Peplink OAuth2 token acquired")

                # Discover org/group/device if not set
                if not self._org_id:
                    await self._discover_device(client)
        except Exception as e:
            logger.warning(f"Peplink token error: {e}")

    async def _discover_device(self, client: httpx.AsyncClient):
        """Auto-discover the first Peplink device (BR1 Pro 5G)."""
        try:
            r = await client.get(
                f"{self.api_url}/rest/o",
                headers={"Authorization": f"Bearer {self._access_token}"},
                timeout=10,
            )
            if r.status_code == 200:
                orgs = r.json().get("data", [])
                if orgs:
                    self._org_id = str(orgs[0]["id"])

                    # Get first group
                    r2 = await client.get(
                        f"{self.api_url}/rest/o/{self._org_id}/g",
                        headers={"Authorization": f"Bearer {self._access_token}"},
                        timeout=10,
                    )
                    if r2.status_code == 200:
                        groups = r2.json().get("data", [])
                        if groups:
                            self._group_id = str(groups[0]["id"])

                            # Get first device
                            r3 = await client.get(
                                f"{self.api_url}/rest/o/{self._org_id}/g/{self._group_id}/d",
                                headers={"Authorization": f"Bearer {self._access_token}"},
                                timeout=10,
                            )
                            if r3.status_code == 200:
                                devices = r3.json().get("data", [])
                                if devices:
                                    self._device_id = str(devices[0]["id"])
                                    logger.info(f"Peplink device discovered: org={self._org_id} group={self._group_id} device={self._device_id}")
        except Exception as e:
            logger.warning(f"Peplink device discovery failed: {e}")

    def _auth_headers(self) -> dict:
        return {"Authorization": f"Bearer {self._access_token}"} if self._access_token else {}

    async def get_wan_status(self) -> dict:
        """Get WAN connection status (Starlink, Cellular 1, Cellular 2)."""
        try:
            async with httpx.AsyncClient() as client:
                await self._ensure_token(client)
                if not self._access_token or not self._device_id:
                    return self._mock_wan_status()

                r = await client.get(
                    f"{self.api_url}/rest/o/{self._org_id}/g/{self._group_id}/d/{self._device_id}",
                    headers=self._auth_headers(),
                    timeout=10,
                )
                if r.status_code == 200:
                    device = r.json().get("data", {})
                    interfaces = device.get("interfaces", [])

                    connections = []
                    active_wan = None
                    failover = False

                    for iface in interfaces:
                        conn = {
                            "name": iface.get("name", "Unknown"),
                            "type": iface.get("type", "unknown"),
                            "status": "connected" if iface.get("status") == "connected" else "standby",
                            "ip": iface.get("ip", ""),
                            "carrier": iface.get("cellular", {}).get("carrier_name", ""),
                            "signal_dbm": iface.get("cellular", {}).get("signal_bar", 0),
                        }
                        connections.append(conn)

                        if conn["status"] == "connected" and not active_wan:
                            active_wan = conn["name"]

                    # Detect failover (active WAN is cellular, not WAN1/Starlink)
                    if active_wan and "cellular" in active_wan.lower():
                        failover = True

                    return {
                        "active_wan": active_wan or "Unknown",
                        "failover_active": failover,
                        "connections": connections,
                    }

                return self._mock_wan_status()
        except Exception as e:
            logger.warning(f"Peplink get_wan_status error: {e}")
            return self._mock_wan_status()

    async def get_data_usage(self) -> dict:
        """Get cellular data usage per SIM."""
        try:
            async with httpx.AsyncClient() as client:
                await self._ensure_token(client)
                if not self._access_token or not self._device_id:
                    return self._mock_data_usage()

                r = await client.get(
                    f"{self.api_url}/rest/o/{self._org_id}/g/{self._group_id}/d/{self._device_id}",
                    headers=self._auth_headers(),
                    timeout=10,
                )
                if r.status_code == 200:
                    device = r.json().get("data", {})
                    interfaces = device.get("interfaces", [])
                    usage = {}
                    for iface in interfaces:
                        if iface.get("type") == "cellular":
                            name = iface.get("name", "cellular")
                            usage[name] = {
                                "used_gb": round(iface.get("cellular", {}).get("data_usage_mb", 0) / 1024, 2),
                                "limit_gb": 50,  # From plan config
                                "carrier": iface.get("cellular", {}).get("carrier_name", "Unknown"),
                            }
                    return usage if usage else self._mock_data_usage()

                return self._mock_data_usage()
        except Exception as e:
            logger.warning(f"Peplink get_data_usage error: {e}")
            return self._mock_data_usage()

    async def get_device_info(self) -> dict:
        """Get device model, firmware, serial."""
        try:
            async with httpx.AsyncClient() as client:
                await self._ensure_token(client)
                if not self._access_token or not self._device_id:
                    return {"model": "BR1 Pro 5G (mock)", "serial": "N/A", "firmware": "N/A"}

                r = await client.get(
                    f"{self.api_url}/rest/o/{self._org_id}/g/{self._group_id}/d/{self._device_id}",
                    headers=self._auth_headers(),
                    timeout=10,
                )
                if r.status_code == 200:
                    d = r.json().get("data", {})
                    return {
                        "model": d.get("product_name", "Unknown"),
                        "serial": d.get("sn", "Unknown"),
                        "firmware": d.get("fw_ver", "Unknown"),
                        "name": d.get("name", ""),
                        "lan_ip": d.get("lan_ip", ""),
                    }
        except Exception as e:
            logger.warning(f"Peplink get_device_info error: {e}")
        return {"model": "BR1 Pro 5G (mock)", "serial": "N/A", "firmware": "N/A"}

    @staticmethod
    def _mock_wan_status() -> dict:
        return {
            "active_wan": "WAN1-Starlink",
            "failover_active": False,
            "connections": [
                {"name": "WAN1-Starlink", "type": "ethernet", "status": "connected",
                 "ip": "100.64.x.x", "carrier": "", "signal_dbm": 0},
                {"name": "Cellular-1", "type": "cellular", "status": "standby",
                 "ip": "", "carrier": "Telus", "signal_dbm": 3},
                {"name": "Cellular-2", "type": "cellular", "status": "standby",
                 "ip": "", "carrier": "Bell", "signal_dbm": 4},
            ],
        }

    @staticmethod
    def _mock_data_usage() -> dict:
        return {
            "cellular_1": {"used_gb": 12.5, "limit_gb": 50, "carrier": "Telus"},
            "cellular_2": {"used_gb": 3.2, "limit_gb": 50, "carrier": "Bell"},
        }


peplink_client = PeplinkClient()
