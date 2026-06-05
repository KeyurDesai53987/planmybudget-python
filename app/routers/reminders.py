from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models import User, Reminder
from app.schemas import ReminderCreate, ReminderUpdate, ReminderResponse
from app.middleware.auth import get_current_user

router = APIRouter()


@router.get("/api/reminders")
async def list_reminders(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Reminder).where(Reminder.userid == user.id).order_by(Reminder.duedate)
    )
    reminders = result.scalars().all()
    return {"reminders": [ReminderResponse.model_validate(r) for r in reminders]}


@router.post("/api/reminders")
async def create_reminder(
    body: ReminderCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    reminder = Reminder(
        userid=user.id,
        title=body.title,
        description=body.description,
        duedate=body.duedate,
        amount=body.amount,
        category=body.category,
        recurring=body.recurring,
        paid=body.paid,
        notify=body.notify,
    )
    db.add(reminder)
    await db.commit()
    await db.refresh(reminder)
    return ReminderResponse.model_validate(reminder)


@router.put("/api/reminders/{reminder_id}")
async def update_reminder(
    reminder_id: str,
    body: ReminderUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Reminder).where(Reminder.id == reminder_id, Reminder.userid == user.id)
    )
    reminder = result.scalar_one_or_none()
    if not reminder:
        raise HTTPException(status_code=404, detail="Reminder not found")

    if body.title is not None:
        reminder.title = body.title
    if body.description is not None:
        reminder.description = body.description
    if body.duedate is not None:
        reminder.duedate = body.duedate
    if body.amount is not None:
        reminder.amount = body.amount
    if body.category is not None:
        reminder.category = body.category
    if body.recurring is not None:
        reminder.recurring = body.recurring
    if body.paid is not None:
        reminder.paid = body.paid
    if body.notify is not None:
        reminder.notify = body.notify

    await db.commit()
    await db.refresh(reminder)
    return ReminderResponse.model_validate(reminder)


@router.delete("/api/reminders/{reminder_id}")
async def delete_reminder(
    reminder_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Reminder).where(Reminder.id == reminder_id, Reminder.userid == user.id)
    )
    reminder = result.scalar_one_or_none()
    if not reminder:
        raise HTTPException(status_code=404, detail="Reminder not found")
    await db.delete(reminder)
    await db.commit()
    return {"message": "Reminder deleted"}
