"""Roof Monitor — WebSocket channel between roof phone and tech at the roulotte.

Flow:
  1. Roof phone connects to /ws/roof/{shoot_id}?token=...&role=publisher
  2. Tech phone connects to /ws/roof/{shoot_id}?token=...&role=subscriber
  3. Every ~2s the roof phone publishes telemetry (JSON)
  4. Server persists a sample (every 30s) and relays ALL to subscribers in real-time
  5. Server computes an adjustment hint and includes it in the relay
"""
import asyncio
import uuid
import time
from datetime import datetime, timezone
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, Query, WebSocket, WebSocketDisconnect, status
from jose import JWTError, jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db, async_session
from app.api.deps import get_current_user, require_tech_or_admin
from app.models.user import User
from app.models.roof_telemetry import RoofTelemetry
from app.schemas.roof import RoofTelemetryIn, RoofTelemetryOut, RoofAdjustmentHint

router = APIRouter(prefix="/roof", tags=["Roof Monitor"])

# ── In-memory state per shoot ──────────────────────────────────────────
_subscribers: dict[str, list[WebSocket]] = {}   # shoot_id → [ws, ...]
_publishers: dict[str, WebSocket] = {}           # shoot_id → ws (one phone per shoot)
_last_persist: dict[str, float] = {}             # shoot_id → epoch
PERSIST_INTERVAL = 30  # seconds between DB writes


def _compute_hint(data: dict) -> dict:
    """Simple heuristic — replace with real algo when Starlink gRPC is wired."""
    obstruction = data.get("obstruction_pct", 0)
    signal = data.get("signal_strength", 0)
    tilt_x = data.get("tilt_x", 0)
    tilt_y = data.get("tilt_y", 0)

    if obstruction < 0.03 and signal > 70:
        return {"action": "hold", "direction": None, "magnitude": None,
                "obstruction_pct": obstruction, "signal_strength": signal,
                "message": "Signal bon — ne touche à rien 👍"}

    # Determine direction from tilt + obstruction
    if abs(tilt_x) > abs(tilt_y):
        direction = "right" if tilt_x > 0 else "left"
    else:
        direction = "backward" if tilt_y > 0 else "forward"

    if obstruction > 0.15:
        magnitude = "large"
    elif obstruction > 0.05:
        magnitude = "moderate"
    else:
        magnitude = "slight"

    msg_map = {
        "left": "← Bouge vers la gauche",
        "right": "→ Bouge vers la droite",
        "forward": "↑ Avance",
        "backward": "↓ Recule",
    }
    message = f"{msg_map[direction]} ({magnitude})"

    return {"action": "adjust", "direction": direction, "magnitude": magnitude,
            "obstruction_pct": obstruction, "signal_strength": signal,
            "message": message}


def _validate_ws_token(token: str) -> dict | None:
    try:
        return jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
    except JWTError:
        return None


# ── WebSocket: the main channel ────────────────────────────────────────
ws_router = APIRouter(tags=["Roof Monitor WS"])


@ws_router.websocket("/ws/roof/{shoot_id}")
async def ws_roof_monitor(websocket: WebSocket, shoot_id: str,
                          token: str = Query(...),
                          role: str = Query("subscriber")):
    payload = _validate_ws_token(token)
    if not payload:
        await websocket.close(code=4001, reason="Invalid token")
        return

    await websocket.accept()

    if role == "publisher":
        _publishers[shoot_id] = websocket
        try:
            while True:
                raw = await websocket.receive_json()
                # Validate
                data = RoofTelemetryIn(**raw).model_dump()
                # Compute hint
                hint = _compute_hint(data)
                # Relay to all subscribers
                envelope = {"type": "roof_telemetry", "shoot_id": shoot_id,
                            "timestamp": datetime.now(timezone.utc).isoformat(),
                            "telemetry": data, "hint": hint}
                dead = []
                for sub in _subscribers.get(shoot_id, []):
                    try:
                        await sub.send_json(envelope)
                    except Exception:
                        dead.append(sub)
                for d in dead:
                    _subscribers[shoot_id].remove(d)
                # Persist sample every PERSIST_INTERVAL
                now = time.time()
                if now - _last_persist.get(shoot_id, 0) >= PERSIST_INTERVAL:
                    _last_persist[shoot_id] = now
                    asyncio.create_task(_persist_telemetry(shoot_id, data))
        except WebSocketDisconnect:
            _publishers.pop(shoot_id, None)

    else:  # subscriber (tech / admin)
        _subscribers.setdefault(shoot_id, []).append(websocket)
        try:
            while True:
                # Subscribers can send commands back (future: "take photo", "reboot")
                await websocket.receive_text()
        except WebSocketDisconnect:
            _subscribers.get(shoot_id, []).remove(websocket) if websocket in _subscribers.get(shoot_id, []) else None


async def _persist_telemetry(shoot_id: str, data: dict):
    """Fire-and-forget DB write for telemetry sample."""
    try:
        async with async_session() as db:
            entry = RoofTelemetry(shoot_id=uuid.UUID(shoot_id), **data)
            db.add(entry)
            await db.commit()
    except Exception as e:
        print(f"[roof] persist error: {e}")


# ── REST endpoints (fallback + history) ────────────────────────────────

@router.get("/status/{shoot_id}")
async def roof_status(shoot_id: str,
                      current_user: Annotated[User, Depends(require_tech_or_admin)]):
    """Is the roof phone currently streaming?"""
    is_live = shoot_id in _publishers
    subs = len(_subscribers.get(shoot_id, []))
    return {"shoot_id": shoot_id, "is_live": is_live, "subscribers": subs}


@router.get("/history/{shoot_id}", response_model=list[RoofTelemetryOut])
async def roof_history(shoot_id: uuid.UUID,
                       current_user: Annotated[User, Depends(require_tech_or_admin)],
                       db: Annotated[AsyncSession, Depends(get_db)],
                       limit: int = Query(60, ge=1, le=500)):
    """Last N telemetry samples (persisted every ~30s)."""
    result = await db.execute(
        select(RoofTelemetry)
        .where(RoofTelemetry.shoot_id == shoot_id)
        .order_by(RoofTelemetry.timestamp.desc())
        .limit(limit)
    )
    return result.scalars().all()


@router.post("/telemetry/{shoot_id}", response_model=RoofTelemetryOut,
             status_code=status.HTTP_201_CREATED)
async def post_telemetry(shoot_id: uuid.UUID,
                         data: RoofTelemetryIn,
                         current_user: Annotated[User, Depends(get_current_user)],
                         db: Annotated[AsyncSession, Depends(get_db)]):
    """REST fallback if WebSocket drops — phone POSTs every few seconds."""
    entry = RoofTelemetry(shoot_id=shoot_id, **data.model_dump())
    db.add(entry)
    await db.commit()
    await db.refresh(entry)
    return entry
