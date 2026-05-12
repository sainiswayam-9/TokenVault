# app/routes/admin.py
# CRUD endpoints for Users, Roles, and Permissions
# These are admin-level operations — protect with auth in production

from fastapi import APIRouter, HTTPException, Request, Depends
from app.models import (
    CreateUserRequest, UpdateUserRequest, UserInDB,
    CreateRoleRequest, UpdateRoleRequest,
    CreatePermissionRequest,
)
from app.auth import hash_password
from app.guards import get_current_user, require_role
from app.config import VALID_ROLES
from app.db import (
    get_all_users, get_user_by_username, get_user_by_id,
    create_user, update_user, delete_user,
    get_all_roles, get_role, create_role, update_role, delete_role,
    get_all_permissions, get_permission, create_permission,
    update_permission, delete_permission,
)

# ── Users — /users ────────────────────────────────────────────────────────────
users_router = APIRouter(prefix="/users", tags=["Users"])


@users_router.get("/")
async def list_users(request: Request):
    """List all users (passwords excluded)."""
    return await get_all_users(request.app.db)


@users_router.get("/{user_id}")
async def get_user(user_id: str, request: Request):
    """Get a single user by ID."""
    user = await get_user_by_id(request.app.db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.pop("hashed_password", None)
    return user


@users_router.post("/", status_code=201)
async def add_user(request: Request, body: CreateUserRequest):
    """Create a new user with an assigned role."""
    db = request.app.db
    if body.role not in VALID_ROLES:
        raise HTTPException(status_code=400, detail=f"Invalid role. Choose: {', '.join(VALID_ROLES)}")
    if await get_user_by_username(db, body.username):
        raise HTTPException(status_code=409, detail="Username already taken")
    if not await get_role(db, body.role):
        raise HTTPException(status_code=400, detail="Role not found in system")

    new_user = UserInDB(
        username=body.username,
        hashed_password=hash_password(body.password),
        role=body.role,
    )
    user_id = await create_user(db, new_user.model_dump())
    return {"message": "User created", "id": user_id, "role": body.role}


@users_router.put("/{user_id}")
async def edit_user(user_id: str, request: Request, body: UpdateUserRequest):
    """Update a user's password, role, or active status."""
    db       = request.app.db
    existing = await get_user_by_id(db, user_id)
    if not existing:
        raise HTTPException(status_code=404, detail="User not found")

    fields = {}
    if body.password is not None:
        fields["hashed_password"] = hash_password(body.password)
    if body.role is not None:
        if body.role not in VALID_ROLES:
            raise HTTPException(status_code=400, detail=f"Invalid role. Choose: {', '.join(VALID_ROLES)}")
        if not await get_role(db, body.role):
            raise HTTPException(status_code=400, detail="Role not found in system")
        fields["role"] = body.role
    if body.is_active is not None:
        fields["is_active"] = body.is_active
    if not fields:
        raise HTTPException(status_code=400, detail="No fields provided to update")

    if not await update_user(db, user_id, fields):
        raise HTTPException(status_code=500, detail="Update failed")
    return {"message": "User updated", "updated_fields": list(fields.keys())}


@users_router.delete("/{user_id}")
async def remove_user(user_id: str, request: Request):
    """Delete a user permanently."""
    if not await get_user_by_id(request.app.db, user_id):
        raise HTTPException(status_code=404, detail="User not found")
    if not await delete_user(request.app.db, user_id):
        raise HTTPException(status_code=500, detail="Delete failed")
    return {"message": "User deleted", "id": user_id}


# ── Roles — /roles ────────────────────────────────────────────────────────────
roles_router = APIRouter(prefix="/roles", tags=["Roles"])


@roles_router.get("/")
async def list_roles(request: Request):
    return await get_all_roles(request.app.db)


@roles_router.get("/{role_name}")
async def get_single_role(role_name: str, request: Request):
    role = await get_role(request.app.db, role_name)
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    return role


@roles_router.post("/", status_code=201)
async def add_role(request: Request, body: CreateRoleRequest):
    """Create a new role with a list of permission keys."""
    db = request.app.db
    if await get_role(db, body.name):
        raise HTTPException(status_code=409, detail="Role already exists")
    for perm_key in body.permissions:
        if not await get_permission(db, perm_key):
            raise HTTPException(status_code=400, detail=f"Permission '{perm_key}' does not exist")
    role_id = await create_role(db, body.name, body.permissions)
    return {"message": "Role created", "id": role_id, "name": body.name}


@roles_router.put("/{role_name}")
async def edit_role(role_name: str, request: Request, body: UpdateRoleRequest):
    """Replace a role's permissions list."""
    db = request.app.db
    if not await get_role(db, role_name):
        raise HTTPException(status_code=404, detail="Role not found")
    for perm_key in body.permissions:
        if not await get_permission(db, perm_key):
            raise HTTPException(status_code=400, detail=f"Permission '{perm_key}' does not exist")
    if not await update_role(db, role_name, body.permissions):
        raise HTTPException(status_code=500, detail="Update failed")
    return {"message": "Role updated", "name": role_name, "permissions": body.permissions}


@roles_router.delete("/{role_name}")
async def remove_role(role_name: str, request: Request):
    if not await get_role(request.app.db, role_name):
        raise HTTPException(status_code=404, detail="Role not found")
    if not await delete_role(request.app.db, role_name):
        raise HTTPException(status_code=500, detail="Delete failed")
    return {"message": "Role deleted", "name": role_name}


# ── Permissions — /permissions ────────────────────────────────────────────────
permissions_router = APIRouter(prefix="/permissions", tags=["Permissions"])


@permissions_router.get("/")
async def list_permissions(request: Request):
    return await get_all_permissions(request.app.db)


@permissions_router.get("/{key}")
async def get_single_permission(key: str, request: Request):
    perm = await get_permission(request.app.db, key)
    if not perm:
        raise HTTPException(status_code=404, detail="Permission not found")
    return perm


@permissions_router.post("/", status_code=201)
async def add_permission(request: Request, body: CreatePermissionRequest):
    db = request.app.db
    if await get_permission(db, body.key):
        raise HTTPException(status_code=409, detail="Permission key already exists")
    perm_id = await create_permission(db, body.key, body.description)
    return {"message": "Permission created", "id": perm_id, "key": body.key}


@permissions_router.put("/{key}")
async def edit_permission(key: str, request: Request, body: CreatePermissionRequest):
    if not await get_permission(request.app.db, key):
        raise HTTPException(status_code=404, detail="Permission not found")
    if not await update_permission(request.app.db, key, body.description):
        raise HTTPException(status_code=500, detail="Update failed")
    return {"message": "Permission updated", "key": key}


@permissions_router.delete("/{key}")
async def remove_permission(key: str, request: Request):
    if not await get_permission(request.app.db, key):
        raise HTTPException(status_code=404, detail="Permission not found")
    if not await delete_permission(request.app.db, key):
        raise HTTPException(status_code=500, detail="Delete failed")
    return {"message": "Permission deleted", "key": key}
