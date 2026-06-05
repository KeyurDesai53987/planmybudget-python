import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Float, Integer, ForeignKey, DateTime, Text
from sqlalchemy.orm import relationship
from app.database import Base


def gen_id():
    return str(uuid.uuid4())


def utcnow():
    return datetime.now(timezone.utc).replace(tzinfo=None)


class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=gen_id)
    email = Column(String, unique=True, nullable=False, index=True)
    passwordhash = Column(String, nullable=False)
    name = Column(String, nullable=True)
    preferredcurrency = Column(String, default="USD")
    locale = Column(String, default="en-US")
    createdat = Column(DateTime, default=utcnow)

    accounts = relationship("Account", back_populates="user")
    categories = relationship("Category", back_populates="user")
    budgets = relationship("Budget", back_populates="user")
    goals = relationship("Goal", back_populates="user")
    sessions = relationship("Session", back_populates="user")
    recurring = relationship("Recurring", back_populates="user")
    api_keys = relationship("ApiKey", back_populates="user")
    reminders = relationship("Reminder", back_populates="user")
    dashboard = relationship("UserDashboard", back_populates="user", uselist=False)


class Account(Base):
    __tablename__ = "accounts"

    id = Column(String, primary_key=True, default=gen_id)
    userid = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    name = Column(String, nullable=False)
    type = Column(String, nullable=False)
    currency = Column(String, default="USD")
    balance = Column(Float, default=0)
    createdat = Column(DateTime, default=utcnow)

    user = relationship("User", back_populates="accounts")
    transactions = relationship("Transaction", back_populates="account")


class Category(Base):
    __tablename__ = "categories"

    id = Column(String, primary_key=True, default=gen_id)
    userId = Column("userid", String, ForeignKey("users.id"), nullable=False, index=True)
    name = Column(String, nullable=False)
    parentId = Column("parentid", String, nullable=True)
    createdat = Column(DateTime, default=utcnow)

    user = relationship("User", back_populates="categories")


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(String, primary_key=True, default=gen_id)
    accountId = Column("accountid", String, ForeignKey("accounts.id"), nullable=False, index=True)
    categoryId = Column("categoryid", String, ForeignKey("categories.id"), nullable=True)
    date = Column(String, nullable=False, index=True)
    amount = Column(Float, nullable=False)
    type = Column(String, nullable=False)
    description = Column(String, nullable=True)
    createdat = Column(DateTime, default=utcnow)

    account = relationship("Account", back_populates="transactions")


class Budget(Base):
    __tablename__ = "budgets"

    id = Column(String, primary_key=True, default=gen_id)
    userId = Column("userid", String, ForeignKey("users.id"), nullable=False, index=True)
    month = Column(Integer, nullable=False)
    year = Column(Integer, nullable=False)
    currency = Column(String, default="USD")
    lines = Column(Text, default="[]")
    createdat = Column(DateTime, default=utcnow)

    user = relationship("User", back_populates="budgets")


class Goal(Base):
    __tablename__ = "goals"

    id = Column(String, primary_key=True, default=gen_id)
    userId = Column("userid", String, ForeignKey("users.id"), nullable=False, index=True)
    name = Column(String, nullable=False)
    targetamount = Column(Float, nullable=False)
    currentamount = Column(Float, default=0)
    duedate = Column(String, nullable=True)
    status = Column(String, default="active")
    createdat = Column(DateTime, default=utcnow)

    user = relationship("User", back_populates="goals")


class Session(Base):
    __tablename__ = "sessions"

    token = Column(String, primary_key=True)
    userid = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    createdat = Column(DateTime, default=utcnow)
    expiresat = Column(DateTime, nullable=True)

    user = relationship("User", back_populates="sessions")


class Recurring(Base):
    __tablename__ = "recurring"

    id = Column(String, primary_key=True, default=gen_id)
    userId = Column("userid", String, ForeignKey("users.id"), nullable=False, index=True)
    accountId = Column("accountid", String, ForeignKey("accounts.id"), nullable=False)
    name = Column(String, nullable=False)
    amount = Column(Float, nullable=False)
    type = Column(String, nullable=False)
    frequency = Column(String, nullable=False)
    startdate = Column(String, nullable=False)
    nextdate = Column(String, nullable=False)
    description = Column(String, nullable=True)
    active = Column(Integer, default=1)
    createdat = Column(DateTime, default=utcnow)

    user = relationship("User", back_populates="recurring")


class ApiKey(Base):
    __tablename__ = "api_keys"

    id = Column(String, primary_key=True, default=gen_id)
    userid = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    name = Column(String, nullable=False)
    keyhash = Column(String, nullable=False)
    keyprefix = Column(String, nullable=False, index=True)
    active = Column(Integer, default=1)
    createdat = Column(DateTime, default=utcnow)

    user = relationship("User", back_populates="api_keys")


class Reminder(Base):
    __tablename__ = "reminders"

    id = Column(String, primary_key=True, default=gen_id)
    userid = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    title = Column(String, nullable=False)
    description = Column(String, nullable=True)
    duedate = Column(String, nullable=False)
    amount = Column(Float, nullable=True)
    category = Column(String, nullable=False)
    recurring = Column(String, nullable=True)
    paid = Column(Integer, default=0)
    notify = Column(Integer, default=1)
    createdat = Column(DateTime, default=utcnow)

    user = relationship("User", back_populates="reminders")


class UserDashboard(Base):
    __tablename__ = "user_dashboard"

    id = Column(String, primary_key=True, default=gen_id)
    userid = Column(String, ForeignKey("users.id"), nullable=False, unique=True, index=True)
    prefs = Column(Text, default="{}")
    createdat = Column(DateTime, default=utcnow)
    updatedat = Column(DateTime, default=utcnow, onupdate=utcnow)

    user = relationship("User", back_populates="dashboard")
