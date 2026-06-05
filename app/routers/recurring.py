from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models import User, Account, Recurring, Transaction
from app.schemas import RecurringCreate, RecurringUpdate, RecurringResponse
from app.middleware.auth import get_current_user
from datetime import datetime, timedelta

router = APIRouter()


def _calc_next_date(frequency: str, from_date: str) -> str:
    try:
        dt = datetime.strptime(from_date, "%Y-%m-%d")
    except ValueError:
        return from_date

    if frequency == "daily":
        dt += timedelta(days=1)
    elif frequency == "weekly":
        dt += timedelta(weeks=1)
    elif frequency == "biweekly":
        dt += timedelta(weeks=2)
    elif frequency == "monthly":
        month = dt.month + 1
        year = dt.year
        if month > 12:
            month = 1
            year += 1
        dt = dt.replace(year=year, month=month)
    elif frequency == "quarterly":
        month = dt.month + 3
        year = dt.year
        if month > 12:
            month -= 12
            year += 1
        dt = dt.replace(year=year, month=month)
    elif frequency == "yearly":
        dt = dt.replace(year=dt.year + 1)
    return dt.strftime("%Y-%m-%d")


@router.get("/api/recurring")
async def list_recurring(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Recurring).where(Recurring.userId == user.id))
    items = result.scalars().all()
    return {"recurring": [RecurringResponse.model_validate(r) for r in items]}


@router.post("/api/recurring")
async def create_recurring(
    body: RecurringCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    account_check = await db.execute(
        select(Account).where(Account.id == body.accountId, Account.userid == user.id)
    )
    if not account_check.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Account not found")

    item = Recurring(
        userId=user.id,
        accountId=body.accountId,
        name=body.name,
        amount=body.amount,
        type=body.type,
        frequency=body.frequency,
        startdate=body.startdate,
        nextdate=body.nextdate,
        description=body.description,
    )
    db.add(item)
    await db.commit()
    await db.refresh(item)
    return RecurringResponse.model_validate(item)


@router.put("/api/recurring/{recurring_id}")
async def update_recurring(
    recurring_id: str,
    body: RecurringUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Recurring).where(Recurring.id == recurring_id, Recurring.userId == user.id)
    )
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="Recurring not found")

    if body.name is not None:
        item.name = body.name
    if body.amount is not None:
        item.amount = body.amount
    if body.type is not None:
        item.type = body.type
    if body.frequency is not None:
        item.frequency = body.frequency
    if body.nextdate is not None:
        item.nextdate = body.nextdate
    if body.description is not None:
        item.description = body.description
    if body.active is not None:
        item.active = body.active

    await db.commit()
    await db.refresh(item)
    return RecurringResponse.model_validate(item)


@router.delete("/api/recurring/{recurring_id}")
async def delete_recurring(
    recurring_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Recurring).where(Recurring.id == recurring_id, Recurring.userId == user.id)
    )
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="Recurring not found")
    await db.delete(item)
    await db.commit()
    return {"message": "Recurring deleted"}


@router.post("/api/recurring/{recurring_id}/process")
async def process_recurring(
    recurring_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Recurring).where(Recurring.id == recurring_id, Recurring.userId == user.id)
    )
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="Recurring not found")

    amount = item.amount
    if item.type == "debit":
        amount = -abs(amount)

    txn = Transaction(
        accountId=item.accountId,
        date=item.nextdate,
        amount=amount,
        type=item.type,
        description=item.name,
    )
    db.add(txn)

    account_result = await db.execute(select(Account).where(Account.id == item.accountId))
    acc = account_result.scalar_one_or_none()
    if acc:
        acc.balance = (acc.balance or 0) + amount

    item.nextdate = _calc_next_date(item.frequency, item.nextdate)
    await db.commit()
    return {"message": "Recurring processed", "nextDate": item.nextdate}
