import asyncio
from backend.database import db
async def main():
    u = await db.users.count_documents({})
    p = await db.projects.count_documents({})
    print(f"Users: {u}, Projects: {p}")
asyncio.run(main())
