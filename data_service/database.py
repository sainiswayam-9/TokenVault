# data_service/database.py
# MongoDB CRUD helpers for sales, reports, and employees

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase

SALES_COL      = "sales"
REPORTS_COL    = "reports"
EMPLOYEES_COL  = "employees"


def _str_id(doc: dict) -> dict:
    """Convert MongoDB _id ObjectId to string in-place."""
    if doc and "_id" in doc:
        doc["_id"] = str(doc["_id"])
    return doc


# ── SALES CRUD ───────────────────────────────────────────────────

async def get_all_sales(db: AsyncIOMotorDatabase, salesperson: str | None = None) -> list[dict]:
    query = {"salesperson": salesperson} if salesperson else {}
    records = []
    async for doc in db[SALES_COL].find(query):
        records.append(_str_id(doc))
    return records


async def get_sale_by_id(db: AsyncIOMotorDatabase, sale_id: str) -> dict | None:
    try:
        doc = await db[SALES_COL].find_one({"_id": ObjectId(sale_id)})
        return _str_id(doc) if doc else None
    except Exception:
        return None


async def create_sale(db: AsyncIOMotorDatabase, data: dict) -> str:
    result = await db[SALES_COL].insert_one(data)
    return str(result.inserted_id)


async def update_sale(db: AsyncIOMotorDatabase, sale_id: str, fields: dict) -> bool:
    try:
        result = await db[SALES_COL].update_one(
            {"_id": ObjectId(sale_id)}, {"$set": fields}
        )
        return result.modified_count == 1
    except Exception:
        return False


async def delete_sale(db: AsyncIOMotorDatabase, sale_id: str) -> bool:
    try:
        result = await db[SALES_COL].delete_one({"_id": ObjectId(sale_id)})
        return result.deleted_count == 1
    except Exception:
        return False


# ── REPORTS CRUD ─────────────────────────────────────────────────

async def get_all_reports(db: AsyncIOMotorDatabase) -> list[dict]:
    records = []
    async for doc in db[REPORTS_COL].find():
        records.append(_str_id(doc))
    return records


async def get_report_by_id(db: AsyncIOMotorDatabase, report_id: str) -> dict | None:
    try:
        doc = await db[REPORTS_COL].find_one({"_id": ObjectId(report_id)})
        return _str_id(doc) if doc else None
    except Exception:
        return None


async def create_report(db: AsyncIOMotorDatabase, data: dict) -> str:
    result = await db[REPORTS_COL].insert_one(data)
    return str(result.inserted_id)


async def update_report(db: AsyncIOMotorDatabase, report_id: str, fields: dict) -> bool:
    try:
        result = await db[REPORTS_COL].update_one(
            {"_id": ObjectId(report_id)}, {"$set": fields}
        )
        return result.modified_count == 1
    except Exception:
        return False


async def delete_report(db: AsyncIOMotorDatabase, report_id: str) -> bool:
    try:
        result = await db[REPORTS_COL].delete_one({"_id": ObjectId(report_id)})
        return result.deleted_count == 1
    except Exception:
        return False


# ── EMPLOYEES CRUD ───────────────────────────────────────────────

async def get_all_employees(db: AsyncIOMotorDatabase) -> list[dict]:
    records = []
    async for doc in db[EMPLOYEES_COL].find():
        records.append(_str_id(doc))
    return records


async def get_employee_by_id(db: AsyncIOMotorDatabase, emp_id: str) -> dict | None:
    try:
        doc = await db[EMPLOYEES_COL].find_one({"_id": ObjectId(emp_id)})
        return _str_id(doc) if doc else None
    except Exception:
        return None


async def create_employee(db: AsyncIOMotorDatabase, data: dict) -> str:
    result = await db[EMPLOYEES_COL].insert_one(data)
    return str(result.inserted_id)


async def update_employee(db: AsyncIOMotorDatabase, emp_id: str, fields: dict) -> bool:
    try:
        result = await db[EMPLOYEES_COL].update_one(
            {"_id": ObjectId(emp_id)}, {"$set": fields}
        )
        return result.modified_count == 1
    except Exception:
        return False


async def delete_employee(db: AsyncIOMotorDatabase, emp_id: str) -> bool:
    try:
        result = await db[EMPLOYEES_COL].delete_one({"_id": ObjectId(emp_id)})
        return result.deleted_count == 1
    except Exception:
        return False
