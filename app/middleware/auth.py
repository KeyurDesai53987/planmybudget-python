from typing import Optional
from fastapi import Request, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models import Session, User, ApiKey
from app.utils.auth import decode_token, verify_api_key

security = HTTPBearer(auto_error=False)


async def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> User:
    auth_header = request.headers.get("Authorization", "")
    api_key_header = request.headers.get("X-API-Key", "")
    token = None

    if api_key_header:
        result = await db.execute(select(ApiKey).where(ApiKey.active == 1))
        api_keys = result.scalars().all()
        for ak in api_keys:
            if verify_api_key(api_key_header, ak.keyhash):
                result = await db.execute(select(User).where(User.id == ak.userid))
                user = result.scalar_one_or_none()
                if user:
                    return user
        raise HTTPException(status_code=401, detail="Invalid API key")

    if auth_header.startswith("Bearer "):
        token = auth_header[7:]
    elif credentials:
        token = credentials.credentials

    if not token:
        raise HTTPException(status_code=401, detail="Authentication required")

    payload = decode_token(token)
    if payload:
        user_id = payload.get("sub")
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if user:
            return user

    result = await db.execute(
        select(Session).where(Session.token == token)
    )
    session = result.scalar_one_or_none()
    if session:
        result = await db.execute(select(User).where(User.id == session.userid))
        user = result.scalar_one_or_none()
        if user:
            return user

    raise HTTPException(status_code=401, detail="Invalid or expired token")
