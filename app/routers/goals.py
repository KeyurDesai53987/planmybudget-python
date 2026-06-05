from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models import User, Goal
from app.schemas import GoalCreate, GoalUpdate, GoalResponse
from app.middleware.auth import get_current_user

router = APIRouter()


@router.get("/api/goals")
async def list_goals(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Goal).where(Goal.userId == user.id))
    goals = result.scalars().all()
    return {"goals": [GoalResponse.model_validate(g) for g in goals]}


@router.post("/api/goals")
async def create_goal(
    body: GoalCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    goal = Goal(
        userId=user.id,
        name=body.name,
        targetamount=body.targetamount,
        currentamount=body.currentamount,
        duedate=body.duedate,
        status=body.status,
    )
    db.add(goal)
    await db.commit()
    await db.refresh(goal)
    return GoalResponse.model_validate(goal)


@router.put("/api/goals/{goal_id}")
async def update_goal(
    goal_id: str,
    body: GoalUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Goal).where(Goal.id == goal_id, Goal.userId == user.id)
    )
    goal = result.scalar_one_or_none()
    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")

    if body.name is not None:
        goal.name = body.name
    if body.targetamount is not None:
        goal.targetamount = body.targetamount
    if body.currentamount is not None:
        goal.currentamount = body.currentamount
    if body.duedate is not None:
        goal.duedate = body.duedate
    if body.status is not None:
        goal.status = body.status

    await db.commit()
    await db.refresh(goal)
    return GoalResponse.model_validate(goal)


@router.delete("/api/goals/{goal_id}")
async def delete_goal(
    goal_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Goal).where(Goal.id == goal_id, Goal.userId == user.id)
    )
    goal = result.scalar_one_or_none()
    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")
    await db.delete(goal)
    await db.commit()
    return {"message": "Goal deleted"}
