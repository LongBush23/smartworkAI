import asyncio
from httpx import AsyncClient, ASGITransport
from backend.main import app
from backend.database import db
import os

os.environ["DB_NAME"] = "smartwork_test_e2e"

async def run_e2e():
    print("Starting E2E Test Workflow...")
    
    # Cleanup DB
    await db.users.delete_many({})
    await db.projects.delete_many({})
    await db.tasks.delete_many({})
    await db.timelogs.delete_many({})
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # 1. Register Manager
        print("1. Registering Manager...")
        res = await client.post("/api/auth/register", json={
            "username": "manager1", "password": "123", "name": "Manager One", "email": "m@example.com", "role": "manager"
        })
        assert res.status_code == 200, res.text
        
        # 2. Register Employees
        print("2. Registering Employees...")
        res = await client.post("/api/auth/register", json={
            "username": "emp1", "password": "123", "name": "Employee One", "email": "e1@example.com", "role": "staff", "skills": ["Python", "React"]
        })
        assert res.status_code == 200, res.text
        
        res = await client.post("/api/auth/register", json={
            "username": "emp2", "password": "123", "name": "Employee Two", "email": "e2@example.com", "role": "staff", "skills": ["UI/UX", "Figma"]
        })
        assert res.status_code == 200, res.text
        
        # 3. Manager Login
        print("3. Manager Login...")
        res = await client.post("/api/auth/login", data={"username": "manager1", "password": "123"})
        assert res.status_code == 200, res.text
        manager_token = res.json()["access_token"]
        manager_headers = {"Authorization": f"Bearer {manager_token}"}
        
        # 4. Manager Creates Project
        print("4. Manager creates project...")
        res = await client.post("/api/projects/", json={
            "name": "E2E Test Project", "description": "Testing the flow",
            "status": "planning", "start_date": "2026-07-01T00:00:00Z", "end_date": "2026-08-01T00:00:00Z"
        }, headers=manager_headers)
        assert res.status_code == 200, res.text
        project_id = res.json()["_id"]
        
        # 5. Manager Creates Tasks
        print("5. Manager creates tasks...")
        res = await client.post("/api/tasks/", json={
            "project_id": project_id, "title": "Setup Backend", "description": "Python API",
            "deadline": "2026-07-15T00:00:00Z", "status": "todo"
        }, headers=manager_headers)
        assert res.status_code == 200, res.text
        task1_id = res.json()["_id"]
        
        res = await client.post("/api/tasks/", json={
            "project_id": project_id, "title": "Design UI", "description": "Figma mockups",
            "deadline": "2026-07-10T00:00:00Z", "status": "todo"
        }, headers=manager_headers)
        assert res.status_code == 200, res.text
        task2_id = res.json()["_id"]
        
        # 6. Manager Gets AI Recommendation
        print("6. Manager calls AI recommendation...")
        res = await client.get(f"/api/ai/optimize-resources/{task1_id}", headers=manager_headers)
        assert res.status_code == 200, res.text
        matches = res.json()
        print(f"   AI Recommendation: {matches}")
        
        # 7. Employee Login
        print("7. Employee Login & Action...")
        res = await client.post("/api/auth/login", data={"username": "emp1", "password": "123"})
        emp1_token = res.json()["access_token"]
        emp1_headers = {"Authorization": f"Bearer {emp1_token}"}
        
        # 8. Employee gets tasks
        res = await client.get("/api/tasks/", headers=emp1_headers)
        assert res.status_code == 200, res.text
        
        # 9. Employee Logs Time
        print("9. Employee logs time...")
        res = await client.post("/api/timelogs/", json={
            "task_id": task1_id,
            "user_id": "emp1",  # Assume API allows this, or it uses token
            "hours": 4.5
        }, headers=emp1_headers)
        assert res.status_code == 200, res.text
        
        print("E2E Test Workflow Completed Successfully!")

if __name__ == "__main__":
    asyncio.run(run_e2e())
