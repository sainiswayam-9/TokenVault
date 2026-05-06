# data_service/models.py
# Pydantic models for data records and JWT

from pydantic import BaseModel, Field
from typing import Optional


# ── JWT ──────────────────────────────────────────────────────────

class TokenData(BaseModel):
    username: str
    role: str


# ── Sales ────────────────────────────────────────────────────────

class CreateSalesRecord(BaseModel):
    product: str = Field(..., min_length=2)
    amount: float = Field(..., gt=0)
    salesperson: str = Field(..., min_length=2)
    date: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}$")  # YYYY-MM-DD


class UpdateSalesRecord(BaseModel):
    product: Optional[str] = None
    amount: Optional[float] = Field(None, gt=0)
    salesperson: Optional[str] = None
    date: Optional[str] = None


# ── Report ───────────────────────────────────────────────────────

class CreateReport(BaseModel):
    period: str = Field(..., min_length=2)       # e.g. "Q3 2024"
    total_revenue: float = Field(..., gt=0)
    top_product: str
    total_deals: int = Field(..., gt=0)


class UpdateReport(BaseModel):
    period: Optional[str] = None
    total_revenue: Optional[float] = Field(None, gt=0)
    top_product: Optional[str] = None
    total_deals: Optional[int] = Field(None, gt=0)


# ── Employee ─────────────────────────────────────────────────────

class CreateEmployee(BaseModel):
    name: str = Field(..., min_length=2)
    department: str
    salary: float = Field(..., gt=0)
    join_date: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}$")


class UpdateEmployee(BaseModel):
    name: Optional[str] = None
    department: Optional[str] = None
    salary: Optional[float] = Field(None, gt=0)
    join_date: Optional[str] = None

