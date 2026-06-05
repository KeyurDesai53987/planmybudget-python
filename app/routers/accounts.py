from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models import User, Account
from app.schemas import AccountCreate, AccountUpdate, AccountResponse
from app.middleware.auth import get_current_user

router = APIRouter()


@router.get("/api/accounts")
async def list_accounts(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Account).where(Account.userid == user.id))
    accounts = result.scalars().all()
    return {"accounts": [AccountResponse.model_validate(a) for a in accounts]}


@router.post("/api/accounts")
async def create_account(
    body: AccountCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    account = Account(
        userid=user.id,
        name=body.name,
        type=body.type,
        currency=body.currency,
    )
    db.add(account)
    await db.commit()
    await db.refresh(account)
    return AccountResponse.model_validate(account)


@router.put("/api/accounts/{account_id}")
async def update_account(
    account_id: str,
    body: AccountUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Account).where(Account.id == account_id, Account.userid == user.id)
    )
    account = result.scalar_one_or_none()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    if body.name is not None:
        account.name = body.name
    if body.type is not None:
        account.type = body.type
    if body.balance is not None:
        account.balance = body.balance

    await db.commit()
    await db.refresh(account)
    return AccountResponse.model_validate(account)


@router.delete("/api/accounts/{account_id}")
async def delete_account(
    account_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Account).where(Account.id == account_id, Account.userid == user.id)
    )
    account = result.scalar_one_or_none()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    await db.delete(account)
    await db.commit()
    return {"message": "Account deleted"}
