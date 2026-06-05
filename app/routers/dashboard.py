from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models import User, UserDashboard
from app.schemas import DashboardPrefsUpdate, DashboardPrefsResponse
from app.middleware.auth import get_current_user

router = APIRouter()


@router.get("/api/dashboard/prefs")
async def get_dashboard_prefs(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(UserDashboard).where(UserDashboard.userid == user.id)
    )
    db_prefs = result.scalar_one_or_none()
    prefs = db_prefs.prefs if db_prefs else "{}"
    return DashboardPrefsResponse(prefs=prefs)


@router.put("/api/dashboard/prefs")
async def update_dashboard_prefs(
    body: DashboardPrefsUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(UserDashboard).where(UserDashboard.userid == user.id)
    )
    db_prefs = result.scalar_one_or_none()
    if db_prefs:
        db_prefs.prefs = body.prefs
    else:
        db_prefs = UserDashboard(userid=user.id, prefs=body.prefs)
        db.add(db_prefs)
    await db.commit()
    return DashboardPrefsResponse(prefs=body.prefs)
