from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional
from datetime import datetime
import json


class UserCreate(BaseModel):
    email: str
    password: str = Field(min_length=6)
    name: Optional[str] = None


class UserLogin(BaseModel):
    email: str
    password: str


class UserResponse(BaseModel):
    id: str
    email: str
    name: Optional[str] = None
    preferredcurrency: str = "USD"
    locale: str = "en-US"
    createdat: Optional[datetime] = None

    @field_validator('preferredcurrency', 'locale', mode='before')
    @classmethod
    def none_to_default(cls, v, info):
        if v is None:
            return "USD" if info.field_name == 'preferredcurrency' else "en-US"
        return v

    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    token: str
    user: UserResponse


class SendOTPRequest(BaseModel):
    email: str


class VerifyOTPRequest(BaseModel):
    email: str
    otp: str
    password: str
    name: Optional[str] = None


class GoogleAuthRequest(BaseModel):
    idToken: str


class ChangePasswordRequest(BaseModel):
    currentPassword: str
    newPassword: str = Field(min_length=6)


class AccountCreate(BaseModel):
    name: str = Field(max_length=100)
    type: str = Field(pattern="^(checking|savings|credit|cash|investment)$")
    currency: str = Field(default="USD", max_length=3, min_length=3)


class AccountUpdate(BaseModel):
    name: Optional[str] = None
    type: Optional[str] = None
    balance: Optional[float] = None


class AccountResponse(BaseModel):
    id: str
    name: str
    type: str
    currency: str
    balance: float
    createdat: Optional[datetime] = None

    model_config = {"from_attributes": True}


class CategoryCreate(BaseModel):
    name: str = Field(max_length=100)
    parentId: Optional[str] = None


class CategoryUpdate(BaseModel):
    name: Optional[str] = None
    parentId: Optional[str] = None


class CategoryResponse(BaseModel):
    id: str
    name: str
    parentId: Optional[str] = None
    createdat: Optional[datetime] = None

    model_config = {"from_attributes": True}


class TransactionCreate(BaseModel):
    accountId: str
    categoryId: Optional[str] = None
    date: str
    amount: float
    type: str = Field(pattern="^(debit|credit)$")
    description: Optional[str] = None


class TransactionUpdate(BaseModel):
    accountId: Optional[str] = None
    categoryId: Optional[str] = None
    date: Optional[str] = None
    amount: Optional[float] = None
    type: Optional[str] = None
    description: Optional[str] = None


class TransactionResponse(BaseModel):
    id: str
    accountId: str
    categoryId: Optional[str] = None
    date: str
    amount: float
    type: str
    description: Optional[str] = None
    createdat: Optional[datetime] = None

    model_config = {"from_attributes": True}


class BudgetLine(BaseModel):
    categoryId: str
    amount: float = 0


class BudgetCreate(BaseModel):
    month: int = Field(ge=1, le=12)
    year: int = Field(ge=2000, le=2100)
    currency: str = "USD"
    lines: list[BudgetLine] = []


class BudgetUpdate(BaseModel):
    lines: Optional[list[BudgetLine]] = None
    currency: Optional[str] = None


class BudgetResponse(BaseModel):
    id: str
    month: int
    year: int
    currency: str
    lines: list[BudgetLine] = []
    createdat: Optional[datetime] = None

    @field_validator('lines', mode='before')
    @classmethod
    def parse_lines(cls, v):
        if isinstance(v, str):
            parsed = json.loads(v)
            for item in parsed:
                if 'budgeted' in item and 'amount' not in item:
                    item['amount'] = item.pop('budgeted')
            return parsed
        if v is None:
            return []
        return v

    model_config = {"from_attributes": True}


class GoalCreate(BaseModel):
    name: str = Field(max_length=200)
    targetamount: float = Field(gt=0)
    currentamount: float = 0
    duedate: Optional[str] = None
    status: str = "active"


class GoalUpdate(BaseModel):
    name: Optional[str] = None
    targetamount: Optional[float] = None
    currentamount: Optional[float] = None
    duedate: Optional[str] = None
    status: Optional[str] = None


class GoalResponse(BaseModel):
    id: str
    name: str
    targetamount: float
    currentamount: float
    duedate: Optional[str] = None
    status: str
    createdat: Optional[datetime] = None

    model_config = {"from_attributes": True}


class RecurringCreate(BaseModel):
    accountId: str
    name: str = Field(max_length=200)
    amount: float
    type: str = Field(pattern="^(debit|credit)$")
    frequency: str
    startdate: str
    nextdate: str
    description: Optional[str] = None


class RecurringUpdate(BaseModel):
    name: Optional[str] = None
    amount: Optional[float] = None
    type: Optional[str] = None
    frequency: Optional[str] = None
    nextdate: Optional[str] = None
    description: Optional[str] = None
    active: Optional[int] = None


class RecurringResponse(BaseModel):
    id: str
    accountId: str
    name: str
    amount: float
    type: str
    frequency: str
    startdate: str
    nextdate: str
    description: Optional[str] = None
    active: int
    createdat: Optional[datetime] = None

    model_config = {"from_attributes": True}


class ReminderCreate(BaseModel):
    title: str = Field(max_length=200)
    description: Optional[str] = None
    duedate: str
    amount: Optional[float] = None
    category: str
    recurring: Optional[str] = None
    paid: int = 0
    notify: int = 1


class ReminderUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    duedate: Optional[str] = None
    amount: Optional[float] = None
    category: Optional[str] = None
    recurring: Optional[str] = None
    paid: Optional[int] = None
    notify: Optional[int] = None


class ReminderResponse(BaseModel):
    id: str
    title: str
    description: Optional[str] = None
    duedate: str
    amount: Optional[float] = None
    category: str
    recurring: Optional[str] = None
    paid: int
    notify: int
    createdat: Optional[datetime] = None

    model_config = {"from_attributes": True}


class ApiKeyCreate(BaseModel):
    name: str = Field(max_length=100)


class ApiKeyResponse(BaseModel):
    id: str
    name: str
    keyprefix: str
    active: int
    createdat: Optional[datetime] = None

    model_config = {"from_attributes": True}


class PreferencesResponse(BaseModel):
    currency: str
    locale: str
    email: str
    name: Optional[str] = None


class PreferencesUpdate(BaseModel):
    currency: Optional[str] = None
    locale: Optional[str] = None
    name: Optional[str] = None


class ProfileResponse(BaseModel):
    id: str
    email: str
    name: Optional[str] = None
    preferredcurrency: str = "USD"
    locale: str = "en-US"

    @field_validator('preferredcurrency', 'locale', mode='before')
    @classmethod
    def none_to_default(cls, v, info):
        if v is None:
            return "USD" if info.field_name == 'preferredcurrency' else "en-US"
        return v

    model_config = {"from_attributes": True}


class DashboardPrefsUpdate(BaseModel):
    prefs: str


class DashboardPrefsResponse(BaseModel):
    prefs: str
