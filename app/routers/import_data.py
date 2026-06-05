import csv
import io
import re
from typing import Optional
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models import User, Account, Transaction, Category
from app.middleware.auth import get_current_user

try:
    import openpyxl
    HAS_OPENPYXL = True
except ImportError:
    HAS_OPENPYXL = False

router = APIRouter()


def detect_delimiter(content: str) -> str:
    try:
        dialect = csv.Sniffer().sniff(content[:1024])
        return dialect.delimiter
    except csv.Error:
        pass
    first_line = content.split('\n')[0].strip()
    comma_count = first_line.count(',')
    semicolon_count = first_line.count(';')
    tab_count = first_line.count('\t')
    if semicolon_count > comma_count and semicolon_count > tab_count:
        return ';'
    if tab_count > comma_count and tab_count > semicolon_count:
        return '\t'
    return ','


def parse_csv(content: str) -> list[dict]:
    delimiter = detect_delimiter(content)
    reader = csv.DictReader(io.StringIO(content), delimiter=delimiter)
    rows = []
    for row in reader:
        cleaned = {}
        for k, v in row.items():
            if k is None:
                continue
            key = k.strip()
            if key:
                cleaned[key] = v.strip() if v else ''
        if cleaned:
            rows.append(cleaned)
    return rows


def parse_excel(content: bytes) -> list[dict]:
    if not HAS_OPENPYXL:
        raise HTTPException(status_code=400, detail="Excel support requires openpyxl")
    wb = openpyxl.load_workbook(io.BytesIO(content), read_only=True)
    ws = wb.active
    rows = list(ws.iter_rows(values_only=True))
    if not rows:
        return []
    headers = [str(h).strip() if h else f"col_{i}" for i, h in enumerate(rows[0])]
    data = []
    for row in rows[1:]:
        row_data = {}
        for i, val in enumerate(row):
            if i < len(headers):
                row_data[headers[i]] = str(val).strip() if val is not None else ""
        data.append(row_data)
    return data


def auto_detect_mapping(headers: list[str]) -> dict:
    mapping = {"date": "", "description": "", "amount": "", "type": "", "category": "", "debit": "", "credit": ""}
    hl = {h.lower(): h for h in headers}

    for key in ["date", "transaction date", "txn date", "posting date", "post date", "time"]:
        if key in hl: mapping["date"] = hl[key]; break
    for key in ["description", "memo", "payee", "name", "note", "merchant", "details", "narrative", "description1"]:
        if key in hl: mapping["description"] = hl[key]; break
    for key in ["amount", "value", "sum", "total", "transaction amount"]:
        if key in hl: mapping["amount"] = hl[key]; break
    for key in ["type", "transaction type", "txn type"]:
        if key in hl: mapping["type"] = hl[key]; break
    for key in ["debit", "withdrawal", "debit amount", "expense", "withdrawals"]:
        if key in hl: mapping["debit"] = hl[key]; break
    for key in ["credit", "deposit", "credit amount", "income", "deposits"]:
        if key in hl: mapping["credit"] = hl[key]; break
    for key in ["category", "category name", "cat", "categoryid", "category1"]:
        if key in hl: mapping["category"] = hl[key]; break

    return mapping


def parse_row(row: dict, mapping: dict, category_map: dict) -> dict:
    result = {"date": "", "description": "", "amount": 0, "type": "debit", "category": "", "category_match": None}

    date_col = mapping.get("date")
    if date_col and date_col in row:
        val = row[date_col]
        val = re.sub(r'[^\d/-]', '', val)
        result["date"] = val

    desc_col = mapping.get("description")
    if desc_col and desc_col in row:
        result["description"] = row[desc_col]

    cat_col = mapping.get("category")
    if cat_col and cat_col in row:
        cat_name = row[cat_col].strip()
        result["category"] = cat_name
        if cat_name.lower() in category_map:
            result["category_match"] = category_map[cat_name.lower()].id

    amount = None
    amount_col = mapping.get("amount")
    debit_col = mapping.get("debit")
    credit_col = mapping.get("credit")

    if amount_col and amount_col in row:
        try:
            amount = float(re.sub(r'[^-\d.]', '', row[amount_col]))
        except (ValueError, TypeError):
            pass

    if amount is not None:
        result["amount"] = abs(amount)
        if amount < 0:
            result["type"] = "debit"
        else:
            result["type"] = "credit"

    if amount is None and debit_col and debit_col in row:
        try:
            d = float(re.sub(r'[^\d.]', '', row[debit_col]))
            if d:
                result["amount"] = d
                result["type"] = "debit"
        except (ValueError, TypeError):
            pass

    if amount is None and credit_col and credit_col in row:
        try:
            c = float(re.sub(r'[^\d.]', '', row[credit_col]))
            if c:
                result["amount"] = c
                result["type"] = "credit"
        except (ValueError, TypeError):
            pass

    type_col = mapping.get("type")
    if type_col and type_col in row:
        type_val = row[type_col].lower()
        if type_val in ("credit", "income", "deposit", "+"):
            result["type"] = "credit"
        elif type_val in ("debit", "expense", "withdrawal", "payment", "-"):
            result["type"] = "debit"

    if not result["date"]:
        result["date"] = ""

    return result


@router.post("/api/transactions/import/preview")
async def preview_import(
    file: UploadFile = File(...),
    dateColumn: str = Form(""),
    descriptionColumn: str = Form(""),
    amountColumn: str = Form(""),
    typeColumn: str = Form(""),
    categoryColumn: str = Form(""),
    debitColumn: str = Form(""),
    creditColumn: str = Form(""),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    filename = file.filename.lower()
    content = await file.read()

    if filename.endswith(".csv"):
        try:
            decoded = content.decode("utf-8-sig")
            rows = parse_csv(decoded)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Failed to parse CSV: {str(e)}")
    elif filename.endswith((".xls", ".xlsx")):
        try:
            rows = parse_excel(content)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Failed to parse Excel: {str(e)}")
    else:
        raise HTTPException(status_code=400, detail="Unsupported format. Please upload CSV or Excel (.xlsx) files.")

    if not rows:
        raise HTTPException(status_code=400, detail="File has no data rows")

    headers = list(rows[0].keys())
    auto = auto_detect_mapping(headers)
    mapping = {
        "date": dateColumn or auto.get("date", ""),
        "description": descriptionColumn or auto.get("description", ""),
        "amount": amountColumn or auto.get("amount", ""),
        "type": typeColumn or auto.get("type", ""),
        "category": categoryColumn or auto.get("category", ""),
        "debit": debitColumn or auto.get("debit", ""),
        "credit": creditColumn or auto.get("credit", ""),
    }

    result = await db.execute(select(Category).where(Category.userId == user.id))
    categories = result.scalars().all()
    category_map = {c.name.lower(): c for c in categories}

    result = await db.execute(select(Account).where(Account.userid == user.id))
    accounts = result.scalars().all()

    preview_rows = []
    errors = []
    for i, row in enumerate(rows[:100]):
        parsed = parse_row(row, mapping, category_map)
        row_errors = []
        if not parsed["date"]:
            row_errors.append("Missing date")
        if parsed["amount"] == 0:
            row_errors.append("Missing amount")
        preview_rows.append({
            "row": i + 1,
            "date": parsed["date"],
            "description": parsed["description"],
            "amount": parsed["amount"],
            "type": parsed["type"],
            "category": parsed["category"],
            "category_match": parsed["category_match"],
            "errors": row_errors,
        })
        if row_errors:
            errors.append({"row": i + 1, "errors": row_errors})

    return {
        "total_rows": len(rows),
        "headers": headers,
        "detected_mapping": mapping,
        "preview": preview_rows,
        "errors": errors,
        "categories": [{"id": c.id, "name": c.name} for c in categories],
        "accounts": [{"id": a.id, "name": a.name, "currency": a.currency} for a in accounts],
    }


@router.post("/api/transactions/import")
async def import_transactions(
    file: UploadFile = File(...),
    accountId: str = Form(...),
    dateColumn: str = Form(""),
    descriptionColumn: str = Form(""),
    amountColumn: str = Form(""),
    typeColumn: str = Form(""),
    categoryColumn: str = Form(""),
    debitColumn: str = Form(""),
    creditColumn: str = Form(""),
    skipHeader: bool = Form(True),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    filename = file.filename.lower()
    content = await file.read()

    if filename.endswith(".csv"):
        try:
            decoded = content.decode("utf-8-sig")
            rows = parse_csv(decoded)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Failed to parse CSV: {str(e)}")
    elif filename.endswith((".xls", ".xlsx")):
        try:
            rows = parse_excel(content)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Failed to parse Excel: {str(e)}")
    else:
        raise HTTPException(status_code=400, detail="Unsupported format")

    if not rows:
        raise HTTPException(status_code=400, detail="No data rows found")

    result = await db.execute(select(Account).where(Account.id == accountId, Account.userid == user.id))
    account = result.scalar_one_or_none()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    result = await db.execute(select(Category).where(Category.userId == user.id))
    categories = result.scalars().all()
    category_map = {c.name.lower(): c for c in categories}

    mapping = {
        "date": dateColumn,
        "description": descriptionColumn,
        "amount": amountColumn,
        "type": typeColumn,
        "category": categoryColumn,
        "debit": debitColumn,
        "credit": creditColumn,
    }

    created = 0
    errors = []
    for i, row in enumerate(rows):
        parsed = parse_row(row, mapping, category_map)
        if not parsed["date"]:
            errors.append({"row": i + 1, "error": "Missing date"})
            continue
        if parsed["amount"] == 0 and not (mapping["debit"] or mapping["credit"]):
            errors.append({"row": i + 1, "error": "Missing amount"})
            continue

        amount = parsed["amount"]
        if parsed["type"] == "debit":
            amount = -abs(amount)
        else:
            amount = abs(amount)

        txn = Transaction(
            accountId=accountId,
            categoryId=parsed["category_match"] or None,
            date=parsed["date"],
            amount=amount,
            type=parsed["type"],
            description=parsed["description"] or None,
        )
        db.add(txn)
        account.balance = (account.balance or 0) + amount
        created += 1

    if created > 0:
        await db.commit()

    return {
        "imported": created,
        "errors": errors,
        "total": len(rows),
        "account_id": accountId,
    }


class ImportRow(BaseModel):
    date: str
    description: str = ""
    amount: float = 0
    type: str = "debit"
    categoryId: Optional[str] = None


class ImportRowsRequest(BaseModel):
    accountId: str
    rows: list[ImportRow]


@router.post("/api/transactions/import/rows")
async def import_transactions_rows(
    body: ImportRowsRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Account).where(Account.id == body.accountId, Account.userid == user.id))
    account = result.scalar_one_or_none()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    created = 0
    errors = []
    for i, row in enumerate(body.rows):
        if not row.date:
            errors.append({"row": i + 1, "error": "Missing date"})
            continue

        amount = row.amount
        if row.type == "debit":
            amount = -abs(amount)
        else:
            amount = abs(amount)

        txn = Transaction(
            accountId=body.accountId,
            categoryId=row.categoryId or None,
            date=row.date,
            amount=amount,
            type=row.type,
            description=row.description or None,
        )
        db.add(txn)
        account.balance = (account.balance or 0) + amount
        created += 1

    if created > 0:
        await db.commit()

    return {
        "imported": created,
        "errors": errors,
        "total": len(body.rows),
        "account_id": body.accountId,
    }
