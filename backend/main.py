from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from backend.routers import auth, projects, employees, tasks, ai, timelogs, task_requests, notifications, comments
from backend.services.seeder import run_seed

app = FastAPI(title="SmartWork AI API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Allow all origins for Vercel deployment
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(projects.router, prefix="/api/projects", tags=["projects"])
app.include_router(employees.router, prefix="/api/employees", tags=["employees"])
app.include_router(tasks.router, prefix="/api/tasks", tags=["tasks"])
app.include_router(task_requests.router, prefix="/api/tasks", tags=["task_requests"])
app.include_router(comments.router, prefix="/api/tasks", tags=["comments"])
app.include_router(notifications.router, prefix="/api/notifications", tags=["notifications"])
app.include_router(timelogs.router, prefix="/api/timelogs", tags=["timelogs"])
app.include_router(ai.router, prefix="/api/ai", tags=["ai"])

# Audit logs endpoint (Admin only)
from fastapi import Depends
from backend.dependencies import require_admin
from backend.database import db
from typing import Optional

@app.get("/api/audit-logs", tags=["audit"])
async def get_audit_logs(
    action: Optional[str] = None,
    target_type: Optional[str] = None,
    limit: int = 50,
    current_user: dict = Depends(require_admin)
):
    query = {}
    if action:
        query["action"] = {"$regex": action, "$options": "i"}
    if target_type:
        query["target_type"] = target_type
    
    cursor = db.audit_logs.find(query).sort("created_at", -1).limit(limit)
    logs = await cursor.to_list(length=limit)
    for log in logs:
        log["_id"] = str(log["_id"])
    return logs

@app.on_event("startup")
async def startup_event():
    print("Backend started")


# Mount frontend
app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")
