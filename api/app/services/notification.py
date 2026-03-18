"""Push notifications via FCM + APNs."""
async def send_push(user_id: str, title: str, body: str) -> bool:
    # TODO: firebase_admin.messaging
    print(f"[PUSH] {user_id}: {title} — {body}")
    return True
