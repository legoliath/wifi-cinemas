"""Starlink Dish gRPC Client — dish status, obstruction data, speed, stow/unstow.

Connects to the dish at 192.168.100.1:9200 via gRPC.
Falls back to mock data if dish is unreachable (dev mode).
"""
import asyncio
import logging
from dataclasses import dataclass
from app.config import settings

logger = logging.getLogger(__name__)

try:
    import grpc
    from google.protobuf import json_format
    HAS_GRPC = True
except ImportError:
    HAS_GRPC = False
    logger.warning("grpcio not installed — Starlink client will use mock data")


@dataclass
class DishStatus:
    state: str  # CONNECTED, SEARCHING, BOOTING, etc.
    uptime_s: int
    downlink_throughput_bps: float
    uplink_throughput_bps: float
    pop_ping_latency_ms: float
    snr: float
    obstruction_pct: float
    obstruction_valid: bool
    alerts: list[str]

    @property
    def download_mbps(self) -> float:
        return round(self.downlink_throughput_bps / 1_000_000, 1)

    @property
    def upload_mbps(self) -> float:
        return round(self.uplink_throughput_bps / 1_000_000, 1)

    def to_dict(self) -> dict:
        return {
            "state": self.state,
            "uptime_s": self.uptime_s,
            "download_mbps": self.download_mbps,
            "upload_mbps": self.upload_mbps,
            "latency_ms": round(self.pop_ping_latency_ms, 1),
            "snr": self.snr,
            "obstruction_pct": round(self.obstruction_pct, 4),
            "obstruction_valid": self.obstruction_valid,
            "alerts": self.alerts,
        }


class StarlinkClient:
    def __init__(self):
        self.dish_address = settings.starlink_dish_address

    async def get_status(self) -> dict:
        """Get dish status via gRPC. Returns dict with normalized fields."""
        if not HAS_GRPC:
            return self._mock_status().to_dict()

        try:
            return await asyncio.wait_for(self._grpc_get_status(), timeout=5.0)
        except Exception as e:
            logger.warning(f"Starlink gRPC failed ({e}), using mock data")
            return self._mock_status().to_dict()

    async def _grpc_get_status(self) -> dict:
        """Real gRPC call to the dish."""
        # Dynamic import — proto modules may not exist yet
        try:
            from spacex.api.device import device_pb2, device_pb2_grpc
        except ImportError:
            logger.warning("Starlink proto modules not found — run grpc_tools to generate them")
            return self._mock_status().to_dict()

        loop = asyncio.get_event_loop()

        def _call():
            with grpc.insecure_channel(self.dish_address) as channel:
                stub = device_pb2_grpc.DeviceStub(channel)
                request = device_pb2.Request(get_status={})
                response = stub.Handle(request, timeout=4)
                status = response.dish_get_status
                alerts = []
                if hasattr(status, 'alerts'):
                    alert_obj = status.alerts
                    for field in alert_obj.DESCRIPTOR.fields:
                        if getattr(alert_obj, field.name, False):
                            alerts.append(field.name)
                return DishStatus(
                    state=device_pb2.DishState.Name(status.state) if hasattr(status, 'state') else "UNKNOWN",
                    uptime_s=int(status.device_state.uptime_s) if hasattr(status, 'device_state') else 0,
                    downlink_throughput_bps=float(status.downlink_throughput_bps),
                    uplink_throughput_bps=float(status.uplink_throughput_bps),
                    pop_ping_latency_ms=float(status.pop_ping_latency_ms),
                    snr=float(status.snr) if hasattr(status, 'snr') else 0.0,
                    obstruction_pct=float(status.obstruction_stats.fraction_obstructed) if hasattr(status, 'obstruction_stats') else 0.0,
                    obstruction_valid=bool(status.obstruction_stats.valid_s > 0) if hasattr(status, 'obstruction_stats') else False,
                    alerts=alerts,
                ).to_dict()

        return await loop.run_in_executor(None, _call)

    async def get_obstruction_data(self) -> dict:
        """Get obstruction map data."""
        status = await self.get_status()
        return {
            "fraction_obstructed": status.get("obstruction_pct", 0),
            "valid": status.get("obstruction_valid", False),
        }

    async def stow(self) -> bool:
        """Stow the dish (transport mode)."""
        if not HAS_GRPC:
            return False
        try:
            from spacex.api.device import device_pb2, device_pb2_grpc
            loop = asyncio.get_event_loop()
            def _call():
                with grpc.insecure_channel(self.dish_address) as channel:
                    stub = device_pb2_grpc.DeviceStub(channel)
                    stub.Handle(device_pb2.Request(dish_stow={}), timeout=5)
                    return True
            return await loop.run_in_executor(None, _call)
        except Exception as e:
            logger.error(f"Stow failed: {e}")
            return False

    async def unstow(self) -> bool:
        """Unstow the dish (operational mode)."""
        if not HAS_GRPC:
            return False
        try:
            from spacex.api.device import device_pb2, device_pb2_grpc
            loop = asyncio.get_event_loop()
            def _call():
                with grpc.insecure_channel(self.dish_address) as channel:
                    stub = device_pb2_grpc.DeviceStub(channel)
                    stub.Handle(device_pb2.Request(dish_stow={"unstow": True}), timeout=5)
                    return True
            return await loop.run_in_executor(None, _call)
        except Exception as e:
            logger.error(f"Unstow failed: {e}")
            return False

    @staticmethod
    def _mock_status() -> DishStatus:
        """Dev/demo mock when dish is unreachable."""
        import random
        return DishStatus(
            state="CONNECTED",
            uptime_s=86400 + random.randint(0, 3600),
            downlink_throughput_bps=random.uniform(80, 220) * 1_000_000,
            uplink_throughput_bps=random.uniform(15, 45) * 1_000_000,
            pop_ping_latency_ms=random.uniform(20, 50),
            snr=random.uniform(7, 12),
            obstruction_pct=random.uniform(0, 0.05),
            obstruction_valid=True,
            alerts=[],
        )


starlink_client = StarlinkClient()
