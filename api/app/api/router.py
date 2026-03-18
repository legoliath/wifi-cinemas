from fastapi import APIRouter
from app.api.v1 import auth, users, shoots, network, alerts, billing, websocket

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(shoots.router)
api_router.include_router(network.router)
api_router.include_router(alerts.router)
api_router.include_router(billing.router)
ws_router = websocket.router
