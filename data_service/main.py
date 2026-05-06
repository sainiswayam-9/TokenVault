# data_service/main.py
# Entry point for the Data Service (runs on port 8001)

from contextlib import asynccontextmanager
from fastapi import FastAPI
from motor.motor_asyncio import AsyncIOMotorClient
from data_service.config import MONGO_URL, DATABASE_NAME
from data_service.routes import me_router, sales_router, reports_router, employees_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.mongo_client = AsyncIOMotorClient(MONGO_URL)
    app.db = app.mongo_client[DATABASE_NAME]
    print(f"[Data Service] Connected to MongoDB: {DATABASE_NAME}")
    yield
    app.mongo_client.close()
    print("[Data Service] MongoDB connection closed")


app = FastAPI(
    title="Data Service",
    description="Role-protected CRUD for Sales, Reports, and Employees. Requires JWT from Auth Service.",
    version="2.0.0",
    lifespan=lifespan,
)

app.include_router(me_router)
app.include_router(sales_router)
app.include_router(reports_router)
app.include_router(employees_router)


@app.get("/")
async def health():
    return {"service": "data", "status": "running", "port": 8001}
