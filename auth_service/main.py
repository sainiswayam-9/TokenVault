# auth_service/main.py
# Entry point for the Auth Service (runs on port 8000)

from contextlib import asynccontextmanager
from fastapi import FastAPI
from motor.motor_asyncio import AsyncIOMotorClient
from auth_service.config import MONGO_URL, DATABASE_NAME
from auth_service.routes import auth_router, users_router, roles_router, permissions_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.mongo_client = AsyncIOMotorClient(MONGO_URL)
    app.db = app.mongo_client[DATABASE_NAME]
    print(f"[Auth Service] Connected to MongoDB: {DATABASE_NAME}")
    yield
    app.mongo_client.close()
    print("[Auth Service] MongoDB connection closed")


app = FastAPI(
    title="Auth Service",
    description="JWT auth + full CRUD for Users, Roles, and Permissions",
    version="2.0.0",
    lifespan=lifespan,
)

app.include_router(auth_router)
app.include_router(users_router)
app.include_router(roles_router)
app.include_router(permissions_router)


@app.get("/")
async def health():
    return {"service": "auth", "status": "running", "port": 8000}
