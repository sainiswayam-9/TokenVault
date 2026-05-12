# app/main.py
# FastAPI application — single entry point (replaces both old services)

from contextlib import asynccontextmanager
from fastapi import FastAPI
from motor.motor_asyncio import AsyncIOMotorClient

from app.config import MONGO_URL, DATABASE_NAME
from app.routes.auth  import router as auth_router
from app.routes.admin import users_router, roles_router, permissions_router
from app.routes.csv   import router as csv_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.mongo_client = AsyncIOMotorClient(MONGO_URL)
    app.db           = app.mongo_client[DATABASE_NAME]
    print(f"[RBAC] Connected to MongoDB: {DATABASE_NAME}")
    yield
    app.mongo_client.close()
    print("[RBAC] MongoDB connection closed")


app = FastAPI(
    title="RBAC API",
    description=(
        "Role-Based Access Control API with JWT authentication and CSV data management.\n\n"
        "**Roles:** `salesperson` · `manager` · `hr`\n\n"
        "**Flow:** Login → copy the `access_token` → click **Authorize** above → use CSV endpoints."
    ),
    version="3.0.0",
    lifespan=lifespan,
)

# ── Route groups ──────────────────────────────────────────────────────────────
app.include_router(auth_router)
app.include_router(users_router)
app.include_router(roles_router)
app.include_router(permissions_router)
app.include_router(csv_router)


@app.get("/", tags=["Health"])
async def health():
    return {"service": "RBAC API", "status": "running", "version": "3.0.0", "port": 8000}
