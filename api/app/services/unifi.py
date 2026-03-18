"""UniFi Controller API Client — manages APs, SSIDs, client tracking."""
import httpx
from app.config import settings

class UniFiClient:
    def __init__(self):
        self.base_url = settings.unifi_controller_url
    async def get_clients(self) -> list[dict]:
        # TODO: GET /proxy/network/api/s/{site}/stat/sta
        return [{"mac":"AA:BB:CC:DD:EE:01","hostname":"iPhone-Production","ap_name":"AP-Roulotte-1"}]
    async def get_access_points(self) -> list[dict]:
        return [{"name":"AP-Roulotte-1","status":"connected","clients":8}]
    async def set_ssid(self, ssid: str, passphrase: str) -> bool:
        # TODO: PUT wlanconf
        return True

unifi_client = UniFiClient()
