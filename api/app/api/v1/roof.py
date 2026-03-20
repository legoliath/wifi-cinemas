"""Roof Monitor — Pull-based: tech requests a snapshot, roof phone responds.

Flow:
  1. Both connect to /ws/roof/{shoot_id}?token=...&role=publisher|subscriber
  2. Roof phone idles (no constant streaming, saves battery)
  3. Tech sends {"type": "request_snapshot"} → server relays to roof phone
  4. Roof phone reads sensors, replies {"type": "snapshot", ...}
  5. Server relays snapshot to tech + persists to DB
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
from app.api.deps import get_current_user, require_admin
from app.models.user import User
from app.models.roof_telemetry import RoofTelemetry
from app.schemas.roof import RoofTelemetryIn, RoofTelemetryOut, RoofAdjustmentHint

router = APIRouter(prefix="/roof", tags=["Roof Monitor"])

# ── In-memory state per shoot ──────────────────────────────────────────
_subscribers: dict[str, list[WebSocket]] = {}   # shoot_id → [tech ws, ...]
_publishers: dict[str, WebSocket] = {}           # shoot_id → roof phone ws


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
    return {"action": "adjust", "direction": direction, "magnitude": magnitude,
            "obstruction_pct": obstruction, "signal_strength": signal,
            "message": f"{msg_map[direction]} ({magnitude})"}


def _validate_ws_token(token: str) -> dict | None:
    try:
        return jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
    except JWTError:
        return None


# ── WebSocket: pull-based channel ──────────────────────────────────────
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
        # ── Roof phone: sits idle, responds to snapshot requests ──
        _publishers[shoot_id] = websocket
        try:
            while True:
                raw = await websocket.receive_json()
                msg_type = raw.get("type")

                if msg_type == "snapshot":
                    # Roof phone is responding to a request
                    data = RoofTelemetryIn(**{k: v for k, v in raw.items() if k != "type"}).model_dump()
                    hint = _compute_hint(data)
                    envelope = {
                        "type": "snapshot_response",
                        "shoot_id": shoot_id,
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "telemetry": data,
                        "hint": hint,
                    }
                    # Relay to all subscribers (tech)
                    dead = []
                    for sub in _subscribers.get(shoot_id, []):
                        try:
                            await sub.send_json(envelope)
                        except Exception:
                            dead.append(sub)
                    for d in dead:
                        _subscribers[shoot_id].remove(d)
                    # Persist every snapshot (they're infrequent now)
                    asyncio.create_task(_persist_telemetry(shoot_id, data))

                # Roof phone can also send heartbeats to confirm it's alive
                elif msg_type == "heartbeat":
                    pass  # just keeps connection alive

        except WebSocketDisconnect:
            _publishers.pop(shoot_id, None)

    else:
        # ── Tech/admin: subscriber — sends requests, receives snapshots ──
        _subscribers.setdefault(shoot_id, []).append(websocket)
        try:
            while True:
                raw = await websocket.receive_json()
                msg_type = raw.get("type")

                if msg_type == "request_snapshot":
                    # Relay request to the roof phone
                    pub = _publishers.get(shoot_id)
                    if pub:
                        try:
                            await pub.send_json({"type": "request_snapshot"})
                        except Exception:
                            await websocket.send_json({
                                "type": "error",
                                "message": "Téléphone-toit déconnecté",
                            })
                            _publishers.pop(shoot_id, None)
                    else:
                        await websocket.send_json({
                            "type": "error",
                            "message": "Aucun téléphone-toit connecté pour ce shoot",
                        })

        except WebSocketDisconnect:
            subs = _subscribers.get(shoot_id, [])
            if websocket in subs:
                subs.remove(websocket)


async def _persist_telemetry(shoot_id: str, data: dict):
    """Fire-and-forget DB write."""
    try:
        async with async_session() as db:
            entry = RoofTelemetry(shoot_id=uuid.UUID(shoot_id), **data)
            db.add(entry)
            await db.commit()
    except Exception as e:
        print(f"[roof] persist error: {e}")


# ── REST endpoints ─────────────────────────────────────────────────────

@router.get("/status/{shoot_id}")
async def roof_status(shoot_id: str,
                      current_user: Annotated[User, Depends(require_admin)]):
    """Is the roof phone currently connected and ready?"""
    is_live = shoot_id in _publishers
    subs = len(_subscribers.get(shoot_id, []))
    return {"shoot_id": shoot_id, "is_live": is_live, "subscribers": subs}


@router.get("/history/{shoot_id}", response_model=list[RoofTelemetryOut])
async def roof_history(shoot_id: uuid.UUID,
                       current_user: Annotated[User, Depends(require_admin)],
                       db: Annotated[AsyncSession, Depends(get_db)],
                       limit: int = Query(60, ge=1, le=500)):
    """Last N snapshots (one per request, not continuous)."""
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
    """REST fallback — POST a snapshot manually."""
    entry = RoofTelemetry(shoot_id=shoot_id, **data.model_dump())
    db.add(entry)
    await db.commit()
    await db.refresh(entry)
    return entry
