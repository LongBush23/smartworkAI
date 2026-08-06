from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from backend.routers import auth, departments, employees, tasks, notifications, comments, kpi, ai

app = FastAPI(
    title="Hệ thống Tính điểm KPI trong Công an nhân dân",
    description="Theo Hướng dẫn số 20-HD/ĐUCA ngày 08/6/2026 của Ban Thường vụ Đảng ủy Công an Trung ương",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Allow all origins for Vercel deployment
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(departments.router, prefix="/api/departments", tags=["departments"])
app.include_router(employees.router, prefix="/api/employees", tags=["employees"])
app.include_router(tasks.router, prefix="/api/tasks", tags=["tasks"])
app.include_router(comments.router, prefix="/api/tasks", tags=["comments"])
app.include_router(notifications.router, prefix="/api/notifications", tags=["notifications"])
app.include_router(kpi.router, tags=["kpi"])
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
