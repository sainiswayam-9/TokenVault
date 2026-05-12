# app/config.py
# All settings loaded from .env — single source of truth

import os
from dotenv import load_dotenv

load_dotenv()

# ── MongoDB ───────────────────────────────────────────────────────────────────
MONGO_URL     = os.getenv("MONGO_URL",     "mongodb://localhost:27017")
DATABASE_NAME = os.getenv("DATABASE_NAME", "rbac_db")

# ── JWT ───────────────────────────────────────────────────────────────────────
SECRET_KEY                 = os.getenv("SECRET_KEY", "super-secret-rbac-key-change-in-prod")
ALGORITHM                  = os.getenv("ALGORITHM",  "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))

# ── RBAC ──────────────────────────────────────────────────────────────────────
VALID_ROLES = {"salesperson", "manager", "hr"}

# ── CSV Storage ───────────────────────────────────────────────────────────────
UPLOADS_DIR = os.getenv("UPLOADS_DIR", "uploads")

# ── CSV Categories ────────────────────────────────────────────────────────────
CSV_PRESET_CATEGORIES = [
	"salon",
	"supermarket",
	"pharmacy",
	"electronics",
	"restaurant",
	"others",
]
