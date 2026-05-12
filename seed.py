# seed.py
# Run once to populate MongoDB with roles, permissions, and sample users.
# Usage: python seed.py

import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from passlib.context import CryptContext

MONGO_URL     = "mongodb://localhost:27017"
DATABASE_NAME = "rbac_db"

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# ── Permissions ───────────────────────────────────────────────────────────────
PERMISSIONS = [
    {"key": "upload_csv",      "description": "Upload CSV data to any category"},
    {"key": "download_csv",    "description": "Download CSV files"},
    {"key": "delete_category", "description": "Delete a category CSV (manager/hr only)"},
    {"key": "view_categories", "description": "List available CSV categories"},
]

# ── Roles ─────────────────────────────────────────────────────────────────────
ROLES = [
    {"name": "salesperson", "permissions": ["upload_csv", "download_csv", "view_categories"]},
    {"name": "manager",     "permissions": ["upload_csv", "download_csv", "view_categories", "delete_category"]},
    {"name": "hr",          "permissions": ["upload_csv", "download_csv", "view_categories", "delete_category"]},
]

# ── Users ─────────────────────────────────────────────────────────────────────
USERS = [
    {"username": "alice",   "password": "alice123",   "role": "salesperson"},
    {"username": "bob",     "password": "bob123",     "role": "salesperson"},
    {"username": "charlie", "password": "charlie123", "role": "salesperson"},
    {"username": "evan",    "password": "evan123",    "role": "manager"},
    {"username": "diana",   "password": "diana123",   "role": "hr"},
]


async def seed():
    client = AsyncIOMotorClient(MONGO_URL)
    db     = client[DATABASE_NAME]

    # Drop all collections for a clean slate
    for col in ["permissions", "roles", "users"]:
        await db[col].drop()
    print("Cleared existing collections.\n")

    # Permissions
    await db["permissions"].insert_many(PERMISSIONS)
    print(f"[OK] {len(PERMISSIONS)} permissions inserted")

    # Roles
    await db["roles"].insert_many(ROLES)
    print(f"[OK] {len(ROLES)} roles inserted: {[r['name'] for r in ROLES]}")

    # Users
    users_to_insert = [
        {
            "username":        u["username"],
            "hashed_password": pwd_context.hash(u["password"]),
            "role":            u["role"],
            "is_active":       True,
        }
        for u in USERS
    ]
    await db["users"].insert_many(users_to_insert)
    print(f"[OK] {len(USERS)} users inserted:")
    for u in USERS:
        print(f"    {u['username']:10s} | role: {u['role']:12s} | password: {u['password']}")

    client.close()
    print("\nSeeding complete!")
    print("\nStart the API:")
    print("   uvicorn app.main:app --port 8000 --reload")
    print("   Open: http://localhost:8000/docs")


if __name__ == "__main__":
    asyncio.run(seed())
