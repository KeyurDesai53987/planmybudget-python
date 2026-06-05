from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models import User
from app.schemas import (
    UserCreate, UserLogin, TokenResponse, UserResponse,
    SendOTPRequest, VerifyOTPRequest, GoogleAuthRequest,
    ChangePasswordRequest,
)
from app.utils.auth import hash_password, verify_password, create_token
from app.utils.email import generate_otp, store_otp, verify_otp, send_email
from app.middleware.auth import get_current_user

router = APIRouter()


@router.post("/api/users/register")
async def register(body: UserCreate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == body.email))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already registered")

    user = User(
        email=body.email,
        passwordhash=hash_password(body.password),
        name=body.name or "",
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    token = create_token(user.id)
    return TokenResponse(
        token=token,
        user=UserResponse.model_validate(user),
    )


@router.post("/api/users/login")
async def login(body: UserLogin, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == body.email))
    user = result.scalar_one_or_none()
    if not user or not verify_password(body.password, user.passwordhash):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    token = create_token(user.id)
    return TokenResponse(
        token=token,
        user=UserResponse.model_validate(user),
    )


@router.post("/api/logout")
async def logout(user: User = Depends(get_current_user)):
    return {"message": "Logged out"}


@router.post("/api/auth/send-otp")
async def send_otp(body: SendOTPRequest):
    otp = generate_otp()
    store_otp(body.email, otp)
    success = await send_email(body.email, "Your OTP Code", f"Your OTP is: {otp}")
    if not success:
        print(f"OTP for {body.email}: {otp}")
    return {"message": "OTP sent"}


@router.post("/api/auth/verify-otp")
async def verify_otp_endpoint(body: VerifyOTPRequest, db: AsyncSession = Depends(get_db)):
    if not verify_otp(body.email, body.otp):
        raise HTTPException(status_code=400, detail="Invalid or expired OTP")

    result = await db.execute(select(User).where(User.email == body.email))
    user = result.scalar_one_or_none()
    if not user:
        user = User(
            email=body.email,
            passwordhash=hash_password(body.password),
            name=body.name or "",
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
    else:
        user.passwordhash = hash_password(body.password)
        await db.commit()

    token = create_token(user.id)
    return TokenResponse(
        token=token,
        user=UserResponse.model_validate(user),
    )


@router.post("/api/auth/google")
async def google_auth(body: GoogleAuthRequest, db: AsyncSession = Depends(get_db)):
    from google.oauth2 import id_token
    from google.auth.transport import requests
    from app.config import get_settings

    settings = get_settings()
    try:
        info = id_token.verify_oauth2_token(body.idToken, requests.Request(), settings.google_client_id)
        email = info.get("email")
        if not email:
            raise HTTPException(status_code=400, detail="Invalid Google token")
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid Google token")

    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    if not user:
        user = User(
            email=email,
            passwordhash=hash_password("google-auth"),
            name=info.get("name", ""),
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)

    token = create_token(user.id)
    return TokenResponse(
        token=token,
        user=UserResponse.model_validate(user),
    )


@router.put("/api/change-password")
async def change_password(
    body: ChangePasswordRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not verify_password(body.currentPassword, user.passwordhash):
        raise HTTPException(status_code=400, detail="Current password is incorrect")
    user.passwordhash = hash_password(body.newPassword)
    await db.commit()
    return {"message": "Password changed"}
