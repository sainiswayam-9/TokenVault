# auth_service/database.py
# MongoDB CRUD helpers for users, roles, and permissions

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase
from auth_service.config import USERS_COLLECTION, ROLES_COLLECTION, PERMISSIONS_COLLECTION
from auth_service.models import UserInDB


# ── USER CRUD ────────────────────────────────────────────────────

async def get_all_users(db: AsyncIOMotorDatabase) -> list[dict]:
    users = []
    async for doc in db[USERS_COLLECTION].find({}, {"hashed_password": 0}):
        doc["_id"] = str(doc["_id"])
        users.append(doc)
    return users


async def get_user_by_username(db: AsyncIOMotorDatabase, username: str) -> dict | None:
    return await db[USERS_COLLECTION].find_one({"username": username})


async def get_user_by_id(db: AsyncIOMotorDatabase, user_id: str) -> dict | None:
    try:
        doc = await db[USERS_COLLECTION].find_one({"_id": ObjectId(user_id)})
        if doc:
            doc["_id"] = str(doc["_id"])
        return doc
    except Exception:
        return None


async def create_user(db: AsyncIOMotorDatabase, user: UserInDB) -> str:
    result = await db[USERS_COLLECTION].insert_one(user.model_dump())
    return str(result.inserted_id)


async def update_user(db: AsyncIOMotorDatabase, user_id: str, fields: dict) -> bool:
    """Update specific fields on a user. Returns True if a document was modified."""
    try:
        result = await db[USERS_COLLECTION].update_one(
            {"_id": ObjectId(user_id)}, {"$set": fields}
        )
        return result.modified_count == 1
    except Exception:
        return False


async def delete_user(db: AsyncIOMotorDatabase, user_id: str) -> bool:
    try:
        result = await db[USERS_COLLECTION].delete_one({"_id": ObjectId(user_id)})
        return result.deleted_count == 1
    except Exception:
        return False


# ── ROLE CRUD ────────────────────────────────────────────────────

async def get_all_roles(db: AsyncIOMotorDatabase) -> list[dict]:
    roles = []
    async for doc in db[ROLES_COLLECTION].find({}, {"_id": 0}):
        roles.append(doc)
    return roles


async def get_role(db: AsyncIOMotorDatabase, role_name: str) -> dict | None:
    return await db[ROLES_COLLECTION].find_one({"name": role_name}, {"_id": 0})


async def create_role(db: AsyncIOMotorDatabase, name: str, permissions: list[str]) -> str:
    result = await db[ROLES_COLLECTION].insert_one({"name": name, "permissions": permissions})
    return str(result.inserted_id)


async def update_role(db: AsyncIOMotorDatabase, role_name: str, permissions: list[str]) -> bool:
    result = await db[ROLES_COLLECTION].update_one(
        {"name": role_name}, {"$set": {"permissions": permissions}}
    )
    return result.modified_count == 1


async def delete_role(db: AsyncIOMotorDatabase, role_name: str) -> bool:
    result = await db[ROLES_COLLECTION].delete_one({"name": role_name})
    return result.deleted_count == 1


# ── PERMISSION CRUD ──────────────────────────────────────────────

async def get_all_permissions(db: AsyncIOMotorDatabase) -> list[dict]:
    perms = []
    async for doc in db[PERMISSIONS_COLLECTION].find({}, {"_id": 0}):
        perms.append(doc)
    return perms


async def get_permission(db: AsyncIOMotorDatabase, key: str) -> dict | None:
    return await db[PERMISSIONS_COLLECTION].find_one({"key": key}, {"_id": 0})


async def create_permission(db: AsyncIOMotorDatabase, key: str, description: str) -> str:
    result = await db[PERMISSIONS_COLLECTION].insert_one({"key": key, "description": description})
    return str(result.inserted_id)


async def update_permission(db: AsyncIOMotorDatabase, key: str, description: str) -> bool:
    result = await db[PERMISSIONS_COLLECTION].update_one(
        {"key": key}, {"$set": {"description": description}}
    )
    return result.modified_count == 1


async def delete_permission(db: AsyncIOMotorDatabase, key: str) -> bool:
    result = await db[PERMISSIONS_COLLECTION].delete_one({"key": key})
    return result.deleted_count == 1
