# seed.py
# Run once to populate MongoDB with roles, permissions, users, and sample data.
# Usage: python seed.py

import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from passlib.context import CryptContext

MONGO_URL = "mongodb://localhost:27017"
DATABASE_NAME = "rbac_db"

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# ── Permissions ──────────────────────────────────────────────────
PERMISSIONS = [
    {"key": "view_own_sales",  "description": "View own sales records only"},
    {"key": "view_all_sales",  "description": "View all sales records across the team"},
    {"key": "view_reports",    "description": "View business summary reports"},
    {"key": "view_employees",  "description": "View employee records and salaries"},
]

# ── Roles ────────────────────────────────────────────────────────
ROLES = [
    {"name": "salesperson", "permissions": ["view_own_sales"]},
    {"name": "manager",     "permissions": ["view_all_sales", "view_reports"]},
    {"name": "hr",          "permissions": ["view_employees"]},
]

# ── Users ────────────────────────────────────────────────────────
USERS = [
    {"username": "alice",   "password": "alice123",   "role": "salesperson"},
    {"username": "bob",     "password": "bob123",     "role": "salesperson"},
    {"username": "charlie", "password": "charlie123", "role": "salesperson"},
    {"username": "evan",    "password": "evan123",    "role": "manager"},
    {"username": "diana",   "password": "diana123",   "role": "hr"},
]

# ── Sample Sales ─────────────────────────────────────────────────
SALES = [
    {"product": "CRM Pro",       "amount": 12000.0, "salesperson": "alice",   "date": "2024-05-01"},
    {"product": "Analytics Hub", "amount": 8500.0,  "salesperson": "bob",     "date": "2024-05-03"},
    {"product": "CRM Pro",       "amount": 15000.0, "salesperson": "alice",   "date": "2024-05-10"},
    {"product": "Data Vault",    "amount": 22000.0, "salesperson": "charlie", "date": "2024-05-12"},
    {"product": "Analytics Hub", "amount": 9800.0,  "salesperson": "bob",     "date": "2024-06-01"},
]

# ── Sample Reports ───────────────────────────────────────────────
REPORTS = [
    {"period": "Q1 2024", "total_revenue": 180000.0, "top_product": "CRM Pro",    "total_deals": 24},
    {"period": "Q2 2024", "total_revenue": 210000.0, "top_product": "Data Vault", "total_deals": 31},
]

# ── Sample Employees ─────────────────────────────────────────────
EMPLOYEES = [
    {"name": "Alice",   "department": "Sales",      "salary": 72000.0, "join_date": "2022-03-15"},
    {"name": "Bob",     "department": "Sales",      "salary": 68000.0, "join_date": "2021-07-01"},
    {"name": "Charlie", "department": "Sales",      "salary": 74000.0, "join_date": "2023-01-20"},
    {"name": "Diana",   "department": "HR",         "salary": 80000.0, "join_date": "2020-11-05"},
    {"name": "Evan",    "department": "Management", "salary": 95000.0, "join_date": "2019-06-10"},
]


async def seed():
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DATABASE_NAME]

    # Drop all collections for a clean slate
    for col in ["permissions", "roles", "users", "sales", "reports", "employees"]:
        await db[col].drop()
    print("Cleared all collections.\n")

    # Permissions
    await db["permissions"].insert_many(PERMISSIONS)
    print(f"✓ {len(PERMISSIONS)} permissions inserted")

    # Roles
    await db["roles"].insert_many(ROLES)
    print(f"✓ {len(ROLES)} roles inserted: {[r['name'] for r in ROLES]}")

    # Users
    users_to_insert = [
        {
            "username": u["username"],
            "hashed_password": pwd_context.hash(u["password"]),
            "role": u["role"],
            "is_active": True,
        }
        for u in USERS
    ]
    await db["users"].insert_many(users_to_insert)
    print(f"✓ {len(USERS)} users inserted:")
    for u in USERS:
        print(f"    {u['username']:10s} | role: {u['role']:12s} | password: {u['password']}")

    # Sales
    await db["sales"].insert_many(SALES)
    print(f"\n✓ {len(SALES)} sales records inserted")

    # Reports
    await db["reports"].insert_many(REPORTS)
    print(f"✓ {len(REPORTS)} reports inserted")

    # Employees
    await db["employees"].insert_many(EMPLOYEES)
    print(f"✓ {len(EMPLOYEES)} employees inserted")

    client.close()
    print("\n✅ Seeding complete! Start both services:")
    print("   uvicorn auth_service.main:app --port 8000 --reload")
    print("   uvicorn data_service.main:app --port 8001 --reload")


if __name__ == "__main__":
    asyncio.run(seed())
