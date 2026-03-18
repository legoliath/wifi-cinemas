"""Firebase Auth — token verification, custom claims."""
async def verify_firebase_token(id_token: str) -> dict | None:
    # TODO: firebase_admin.auth.verify_id_token(id_token)
    return {"uid": "dev-user", "email": "dev@wificinemas.com"}

async def set_custom_claims(uid: str, claims: dict) -> bool:
    # TODO: auth.set_custom_user_claims(uid, claims)
    return True
