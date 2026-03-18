import asyncio, random
from datetime import datetime, timezone
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from jose import JWTError, jwt
from app.config import settings

router = APIRouter(tags=["WebSocket"])
connections: dict[str, list[WebSocket]] = {}

@router.websocket("/ws/metrics/{shoot_id}")
async def websocket_metrics(websocket: WebSocket, shoot_id: str, token: str = Query(...)):
    try:
        jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
    except JWTError:
        await websocket.close(code=4001, reason="Invalid token")
        return
    await websocket.accept()
    connections.setdefault(shoot_id, []).append(websocket)
    try:
        while True:
            await websocket.send_json({"type":"metrics","shoot_id":shoot_id,"timestamp":datetime.now(timezone.utc).isoformat(),"download_mbps":round(random.uniform(80,220),1),"upload_mbps":round(random.uniform(15,45),1),"latency_ms":round(random.uniform(18,50),1),"packet_loss":round(random.uniform(0,0.8),2),"source":random.choice(["starlink","starlink","starlink","5g"]),"is_failover":random.random()<0.05,"connected_devices":random.randint(5,30)})
            await asyncio.sleep(2)
    except WebSocketDisconnect:
        connections[shoot_id].remove(websocket)
