from motor.motor_asyncio import AsyncIOMotorClient
import os
import certifi

MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = os.getenv("DB_NAME", "smartwork")

client = AsyncIOMotorClient(MONGO_URI, tlsCAFile=certifi.where())
db = client[DB_NAME]

def get_db():
    return db
