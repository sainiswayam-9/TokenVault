# auth_service/config.py
# All settings for the auth service in one place

MONGO_URL = "mongodb://localhost:27017"
DATABASE_NAME = "rbac_db"

# JWT settings - change SECRET_KEY in production!
SECRET_KEY = "super-secret-rbac-key-change-in-prod"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

# Collections
USERS_COLLECTION = "users"
ROLES_COLLECTION = "roles"
PERMISSIONS_COLLECTION = "permissions"
