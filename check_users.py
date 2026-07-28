import asyncio
from backend.database import db

async def check():
    users = await db.users.find({}).to_list(length=10)
    for u in users:
        print(f"Email: {u.get('email')}, Username: {u.get('username')}")

if __name__ == "__main__":
    asyncio.run(check())
