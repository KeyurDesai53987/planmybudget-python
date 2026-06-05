from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models import User, Account, Transaction
from app.schemas import TransactionCreate, TransactionUpdate, TransactionResponse
from app.middleware.auth import get_current_user

router = APIRouter()


@router.get("/api/transactions")
async def list_transactions(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Transaction)
        .join(Account, Transaction.accountId == Account.id)
        .where(Account.userid == user.id)
        .order_by(Transaction.date.desc(), Transaction.createdat.desc())
    )
    transactions = result.scalars().all()
    return {"transactions": [TransactionResponse.model_validate(t) for t in transactions]}


@router.post("/api/transactions")
async def create_transaction(
    body: TransactionCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Account).where(Account.id == body.accountId, Account.userid == user.id)
    )
    account = result.scalar_one_or_none()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    amount = body.amount
    if body.type == "debit":
        amount = -abs(amount)
    else:
        amount = abs(amount)

    txn = Transaction(
        accountId=body.accountId,
        categoryId=body.categoryId,
        date=body.date,
        amount=amount,
        type=body.type,
        description=body.description,
    )
    db.add(txn)

    account.balance = (account.balance or 0) + amount
    await db.commit()
    await db.refresh(txn)
    return TransactionResponse.model_validate(txn)


@router.put("/api/transactions/{transaction_id}")
async def update_transaction(
    transaction_id: str,
    body: TransactionUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Transaction)
        .join(Account, Transaction.accountId == Account.id)
        .where(Transaction.id == transaction_id, Account.userid == user.id)
    )
    txn = result.scalar_one_or_none()
    if not txn:
        raise HTTPException(status_code=404, detail="Transaction not found")

    old_amount = txn.amount

    if body.accountId is not None:
        txn.accountId = body.accountId
    if body.categoryId is not None:
        txn.categoryId = body.categoryId
    if body.date is not None:
        txn.date = body.date
    if body.description is not None:
        txn.description = body.description
    if body.amount is not None:
        txn.amount = body.amount
    if body.type is not None:
        txn.type = body.type

    await db.commit()
    await db.refresh(txn)

    if body.amount is not None or body.type is not None:
        result = await db.execute(select(Account).where(Account.id == txn.accountId))
        account = result.scalar_one_or_none()
        if account:
            account.balance = (account.balance or 0) - old_amount + txn.amount
            await db.commit()

    return TransactionResponse.model_validate(txn)


@router.delete("/api/transactions/{transaction_id}")
async def delete_transaction(
    transaction_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Transaction)
        .join(Account, Transaction.accountId == Account.id)
        .where(Transaction.id == transaction_id, Account.userid == user.id)
    )
    txn = result.scalar_one_or_none()
    if not txn:
        raise HTTPException(status_code=404, detail="Transaction not found")

    result = await db.execute(select(Account).where(Account.id == txn.accountId))
    account = result.scalar_one_or_none()
    if account:
        account.balance = (account.balance or 0) - txn.amount

    await db.delete(txn)
    await db.commit()
    return {"message": "Transaction deleted"}
