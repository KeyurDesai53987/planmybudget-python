from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models import User, ApiKey
from app.schemas import PreferencesResponse, PreferencesUpdate, ProfileResponse, ApiKeyCreate, ApiKeyResponse
from app.middleware.auth import get_current_user
from app.utils.auth import generate_api_key

router = APIRouter()


@router.get("/api/profile")
async def get_profile(
    user: User = Depends(get_current_user),
):
    return ProfileResponse.model_validate(user)


@router.put("/api/profile")
async def update_profile(
    body: PreferencesUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if body.name is not None:
        user.name = body.name
    if body.currency is not None:
        user.preferredcurrency = body.currency
    if body.locale is not None:
        user.locale = body.locale
    await db.commit()
    await db.refresh(user)
    return ProfileResponse.model_validate(user)


@router.get("/api/preferences")
async def get_preferences(
    user: User = Depends(get_current_user),
):
    return PreferencesResponse(
        currency=user.preferredcurrency,
        locale=user.locale,
        email=user.email,
        name=user.name,
    )


@router.put("/api/preferences")
async def update_preferences(
    body: PreferencesUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if body.currency is not None:
        user.preferredcurrency = body.currency
    if body.locale is not None:
        user.locale = body.locale
    if body.name is not None:
        user.name = body.name
    await db.commit()
    await db.refresh(user)
    return PreferencesResponse(
        currency=user.preferredcurrency,
        locale=user.locale,
        email=user.email,
        name=user.name,
    )


@router.post("/api/api-keys")
async def create_api_key(
    body: ApiKeyCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    key, prefix, key_hash = generate_api_key()
    api_key = ApiKey(
        userid=user.id,
        name=body.name,
        keyhash=key_hash,
        keyprefix=prefix,
    )
    db.add(api_key)
    await db.commit()
    return {"id": api_key.id, "name": api_key.name, "key": key, "keyprefix": prefix}


@router.get("/api/api-keys")
async def list_api_keys(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(ApiKey).where(ApiKey.userid == user.id))
    keys = result.scalars().all()
    return {"api_keys": [ApiKeyResponse.model_validate(k) for k in keys]}


@router.delete("/api/api-keys/{key_id}")
async def delete_api_key(
    key_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(ApiKey).where(ApiKey.id == key_id, ApiKey.userid == user.id)
    )
    api_key = result.scalar_one_or_none()
    if not api_key:
        raise HTTPException(status_code=404, detail="API key not found")
    await db.delete(api_key)
    await db.commit()
    return {"message": "API key deleted"}
