# data_service/config.py
# Settings for the data service

MONGO_URL = "mongodb://localhost:27017"
DATABASE_NAME = "rbac_db"

# Must match auth_service/config.py exactly so JWT verification works
SECRET_KEY = "super-secret-rbac-key-change-in-prod"
ALGORITHM = "HS256"
