# app/db.py
# MongoDB connection helpers — users, roles, permissions CRUD

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase


def _to_dict(doc: dict) -> dict:
    """Convert MongoDB document: replace _id with string id."""
    if doc:
        doc["id"] = str(doc.pop("_id"))
    return doc


# ── Users ─────────────────────────────────────────────────────────────────────

async def get_all_users(db: AsyncIOMotorDatabase):
    users = []
    async for u in db.users.find({}, {"hashed_password": 0}):
        users.append(_to_dict(u))
    return users


async def get_user_by_username(db, username: str):
    return await db.users.find_one({"username": username})


async def get_user_by_id(db, user_id: str):
    try:
        return await db.users.find_one({"_id": ObjectId(user_id)})
    except Exception:
        return None


async def create_user(db, user_dict: dict) -> str:
    result = await db.users.insert_one(user_dict)
    return str(result.inserted_id)


async def update_user(db, user_id: str, fields: dict) -> bool:
    try:
        result = await db.users.update_one({"_id": ObjectId(user_id)}, {"$set": fields})
        return result.modified_count > 0
    except Exception:
        return False


async def delete_user(db, user_id: str) -> bool:
    try:
        result = await db.users.delete_one({"_id": ObjectId(user_id)})
        return result.deleted_count > 0
    except Exception:
        return False


# ── Roles ─────────────────────────────────────────────────────────────────────

async def get_all_roles(db):
    roles = []
    async for r in db.roles.find({}):
        roles.append(_to_dict(r))
    return roles


async def get_role(db, name: str):
    return await db.roles.find_one({"name": name})


async def create_role(db, name: str, permissions: list) -> str:
    result = await db.roles.insert_one({"name": name, "permissions": permissions})
    return str(result.inserted_id)


async def update_role(db, name: str, permissions: list) -> bool:
    result = await db.roles.update_one({"name": name}, {"$set": {"permissions": permissions}})
    return result.modified_count > 0


async def delete_role(db, name: str) -> bool:
    result = await db.roles.delete_one({"name": name})
    return result.deleted_count > 0


# ── Permissions ───────────────────────────────────────────────────────────────

async def get_all_permissions(db):
    perms = []
    async for p in db.permissions.find({}):
        perms.append(_to_dict(p))
    return perms


async def get_permission(db, key: str):
    return await db.permissions.find_one({"key": key})


async def create_permission(db, key: str, description: str) -> str:
    result = await db.permissions.insert_one({"key": key, "description": description})
    return str(result.inserted_id)


async def update_permission(db, key: str, description: str) -> bool:
    result = await db.permissions.update_one({"key": key}, {"$set": {"description": description}})
    return result.modified_count > 0


async def delete_permission(db, key: str) -> bool:
    result = await db.permissions.delete_one({"key": key})
    return result.deleted_count > 0
