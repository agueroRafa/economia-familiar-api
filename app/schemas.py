from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class UserCreate(BaseModel):
    email: EmailStr
    full_name: str = Field(min_length=2, max_length=255)
    password: str = Field(min_length=6, max_length=128)


class UserOut(BaseModel):
    id: int
    email: EmailStr
    full_name: str
    created_at: datetime

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str


class ExpenseBase(BaseModel):
    title: str
    description: Optional[str] = None
    amount: float
    due_date: Optional[str] = None
    assigned_to_user_id: Optional[int] = None
    paid_by_user_id: Optional[int] = None


class ExpenseCreate(ExpenseBase):
    pass


class ExpenseOut(ExpenseBase):
    id: int
    created_by_user_id: int
    created_at: datetime

    class Config:
        from_attributes = True


class DebtBase(BaseModel):
    creditor: str
    description: Optional[str] = None
    amount: float
    due_date: Optional[str] = None
    status: str = "pending"
    assigned_to_user_id: Optional[int] = None
    paid_by_user_id: Optional[int] = None


class DebtCreate(DebtBase):
    pass


class DebtOut(DebtBase):
    id: int
    created_by_user_id: int
    created_at: datetime

    class Config:
        from_attributes = True


class IncomeBase(BaseModel):
    source: str
    description: Optional[str] = None
    amount: float
    income_date: Optional[str] = None
    assigned_to_user_id: Optional[int] = None


class IncomeCreate(IncomeBase):
    pass


class IncomeOut(IncomeBase):
    id: int
    created_by_user_id: int
    created_at: datetime

    class Config:
        from_attributes = True


class EventBase(BaseModel):
    title: str
    description: Optional[str] = None
    event_datetime: str
    location: Optional[str] = None
    assigned_to_user_id: Optional[int] = None


class EventCreate(EventBase):
    pass


class EventOut(EventBase):
    id: int
    created_by_user_id: int
    created_at: datetime

    class Config:
        from_attributes = True


class AttachmentOut(BaseModel):
    id: int
    kind: str
    original_filename: str
    saved_path: str
    mime_type: Optional[str] = None
    uploaded_at: datetime
    uploaded_by_user_id: int
    expense_id: Optional[int] = None
    debt_id: Optional[int] = None
    income_id: Optional[int] = None

    class Config:
        from_attributes = True


class DashboardOut(BaseModel):
    total_expenses: float
    total_debts: float
    total_incomes: float
    balance: float
