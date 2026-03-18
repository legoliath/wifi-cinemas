"""Peplink InControl2 API — WAN monitoring, failover, data usage."""
import httpx
from app.config import settings

class PeplinkClient:
    def __init__(self):
        self.api_url = settings.peplink_ic2_api_url
    async def get_wan_status(self) -> dict:
        return {"active_wan":"WAN1-Starlink","failover_active":False,"connections":[{"name":"WAN1-Starlink","status":"connected"},{"name":"Cellular-1","status":"standby","carrier":"Telus"},{"name":"Cellular-2","status":"standby","carrier":"Bell"}]}
    async def get_data_usage(self) -> dict:
        return {"cellular_1":{"used_gb":12.5,"limit_gb":50},"cellular_2":{"used_gb":3.2,"limit_gb":50}}

peplink_client = PeplinkClient()
