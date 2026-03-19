from fastapi import APIRouter
from app.api.v1 import auth, users, shoots, network, alerts, billing, websocket, roof, kits

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(shoots.router)
api_router.include_router(network.router)
api_router.include_router(alerts.router)
api_router.include_router(billing.router)
api_router.include_router(roof.router)
api_router.include_router(kits.router)
ws_router = websocket.router
ws_roof_router = roof.ws_router
