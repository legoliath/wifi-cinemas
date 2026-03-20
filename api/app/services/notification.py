"""Push notifications via Firebase Cloud Messaging (FCM).

Sends alerts to tech/admin when:
- Starlink goes down → failover active
- AP goes offline
- Data cap warning (80%+)
- High latency / packet loss
"""
import logging
from typing import Optional
from app.config import settings

logger = logging.getLogger(__name__)

try:
    import firebase_admin
    from firebase_admin import credentials, messaging
    HAS_FIREBASE = True
except ImportError:
    HAS_FIREBASE = False

_firebase_initialized = False


def _init_firebase():
    global _firebase_initialized
    if _firebase_initialized or not HAS_FIREBASE:
        return
    try:
        if settings.firebase_service_account_path:
            cred = credentials.Certificate(settings.firebase_service_account_path)
            firebase_admin.initialize_app(cred)
            _firebase_initialized = True
            logger.info("Firebase initialized")
    except Exception as e:
        logger.warning(f"Firebase init failed: {e}")


async def send_push(
    token: str,
    title: str,
    body: str,
    data: Optional[dict] = None,
) -> bool:
    """Send push notification to a single device token."""
    if not HAS_FIREBASE:
        logger.info(f"[PUSH mock] {title}: {body}")
        return True

    _init_firebase()
    if not _firebase_initialized:
        logger.info(f"[PUSH mock] {title}: {body}")
        return True

    try:
        message = messaging.Message(
            notification=messaging.Notification(title=title, body=body),
            data=data or {},
            token=token,
        )
        messaging.send(message)
        logger.info(f"Push sent: {title}")
        return True
    except Exception as e:
        logger.error(f"Push failed: {e}")
        return False


async def send_topic_push(
    topic: str,
    title: str,
    body: str,
    data: Optional[dict] = None,
) -> bool:
    """Send push to all subscribers of a topic (e.g., 'shoot_{shoot_id}_alerts')."""
    if not HAS_FIREBASE or not _firebase_initialized:
        _init_firebase()

    if not _firebase_initialized:
        logger.info(f"[PUSH mock] topic={topic}: {title}: {body}")
        return True

    try:
        message = messaging.Message(
            notification=messaging.Notification(title=title, body=body),
            data=data or {},
            topic=topic,
        )
        messaging.send(message)
        logger.info(f"Topic push sent: {topic} — {title}")
        return True
    except Exception as e:
        logger.error(f"Topic push failed: {e}")
        return False


# Alert-specific helpers
async def notify_failover(shoot_id: str, from_wan: str, to_wan: str):
    await send_topic_push(
        topic=f"shoot_{shoot_id}_alerts",
        title="⚠️ Failover activé",
        body=f"Connexion basculée de {from_wan} vers {to_wan}",
        data={"type": "failover", "shoot_id": shoot_id},
    )


async def notify_ap_offline(shoot_id: str, ap_name: str):
    await send_topic_push(
        topic=f"shoot_{shoot_id}_alerts",
        title="🔴 AP hors ligne",
        body=f"L'access point {ap_name} ne répond plus",
        data={"type": "ap_offline", "shoot_id": shoot_id, "ap_name": ap_name},
    )


async def send_invite_email(
    to_email: str,
    to_name: str,
    shoot_name: str,
    inviter_name: str,
    invite_url: str,
) -> bool:
    """Send an invitation email. Uses SMTP or a transactional email service."""
    # TODO: Replace with real email service (SendGrid, SES, Resend, etc.)
    logger.info(
        f"[EMAIL] Invite → {to_email}: {inviter_name} vous invite au tournage '{shoot_name}'. "
        f"Lien: {invite_url}"
    )
    return True


async def notify_data_cap(shoot_id: str, carrier: str, used_gb: float, limit_gb: float):
    pct = round(used_gb / limit_gb * 100)
    await send_topic_push(
        topic=f"shoot_{shoot_id}_alerts",
        title=f"📊 Data {carrier}: {pct}%",
        body=f"{used_gb:.1f} GB / {limit_gb} GB utilisés",
        data={"type": "data_cap", "shoot_id": shoot_id, "carrier": carrier},
    )
