from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models import User, Budget
from app.schemas import BudgetCreate, BudgetUpdate, BudgetResponse
from app.middleware.auth import get_current_user
import json

router = APIRouter()


@router.get("/api/budgets")
async def list_budgets(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Budget).where(Budget.userId == user.id))
    budgets = result.scalars().all()
    return {"budgets": [BudgetResponse.model_validate(b) for b in budgets]}


@router.get("/api/budgets/alerts")
async def get_budget_alerts(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    from datetime import datetime
    now = datetime.utcnow()
    result = await db.execute(
        select(Budget).where(
            Budget.userId == user.id,
            Budget.month == now.month,
            Budget.year == now.year,
        )
    )
    budget = result.scalar_one_or_none()
    if not budget:
        return {"alerts": []}

    from app.models import Transaction, Account
    lines = json.loads(budget.lines)
    alerts = []
    for line in lines:
        cat_id = line.get("categoryId")
        budgeted = line.get("budgeted", 0)
        txn_result = await db.execute(
            select(Transaction)
            .join(Account, Transaction.accountId == Account.id)
            .where(
                Account.userid == user.id,
                Transaction.categoryId == cat_id,
                Transaction.amount < 0,
            )
        )
        txns = txn_result.scalars().all()
        spent = sum(abs(t.amount) for t in txns)

        if spent > budgeted:
            alerts.append({
                "categoryId": cat_id,
                "budgeted": budgeted,
                "spent": spent,
                "over": spent - budgeted,
            })

    return {"alerts": alerts}


@router.post("/api/budgets/send-alert")
async def send_budget_alert(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return {"message": "Alert sent"}


@router.post("/api/budgets")
async def create_budget(
    body: BudgetCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    existing = await db.execute(
        select(Budget).where(
            Budget.userId == user.id,
            Budget.month == body.month,
            Budget.year == body.year,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Budget already exists for this month")

    budget = Budget(
        userId=user.id,
        month=body.month,
        year=body.year,
        currency=body.currency,
        lines=json.dumps([l.model_dump() for l in body.lines]),
    )
    db.add(budget)
    await db.commit()
    await db.refresh(budget)
    return BudgetResponse.model_validate(budget)


@router.put("/api/budgets/{budget_id}")
async def update_budget(
    budget_id: str,
    body: BudgetUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Budget).where(Budget.id == budget_id, Budget.userId == user.id)
    )
    budget = result.scalar_one_or_none()
    if not budget:
        raise HTTPException(status_code=404, detail="Budget not found")
    if body.lines is not None:
        budget.lines = json.dumps([l.model_dump() for l in body.lines])
    if body.currency is not None:
        budget.currency = body.currency
    await db.commit()
    await db.refresh(budget)
    return BudgetResponse.model_validate(budget)


@router.delete("/api/budgets/{budget_id}")
async def delete_budget(
    budget_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Budget).where(Budget.id == budget_id, Budget.userId == user.id)
    )
    budget = result.scalar_one_or_none()
    if not budget:
        raise HTTPException(status_code=404, detail="Budget not found")
    await db.delete(budget)
    await db.commit()
    return {"message": "Budget deleted"}
