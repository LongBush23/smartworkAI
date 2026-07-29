from motor.motor_asyncio import AsyncIOMotorClient
import certifi

from backend.config import MONGO_URI, DB_NAME

# Kết nối MongoDB Atlas cần TLS; MongoDB cục bộ thì không.
if MONGO_URI and MONGO_URI.startswith("mongodb+srv"):
    client = AsyncIOMotorClient(MONGO_URI, tlsCAFile=certifi.where())
else:
    client = AsyncIOMotorClient(MONGO_URI or "mongodb://localhost:27017")

db = client[DB_NAME]


def get_db():
    return db
