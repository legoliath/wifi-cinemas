"""Starlink Dish gRPC Client — dish status, obstruction data, signal quality."""
from app.config import settings

class StarlinkClient:
    def __init__(self):
        self.dish_address = settings.starlink_dish_address
    async def get_status(self) -> dict:
        # TODO: gRPC DishGetStatusRequest
        return {"state":"CONNECTED","uptime_s":86400,"downlink_throughput_bps":150000000,"uplink_throughput_bps":25000000,"pop_ping_latency_ms":25.0,"snr":9.0}
    async def get_obstruction_data(self) -> dict:
        return {"fraction_obstructed":0.02,"valid":True}

starlink_client = StarlinkClient()
