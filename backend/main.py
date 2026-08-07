import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from backend.config import nguon_cors
from backend.routers import auth, departments, employees, tasks, notifications, comments, kpi, ai

app = FastAPI(
    title="Hệ thống Tính điểm KPI trong Công an nhân dân",
    description="Theo Hướng dẫn số 20-HD/ĐUCA ngày 08/6/2026 của Ban Thường vụ Đảng ủy Công an Trung ương",
)

# Nguồn được phép gọi API: máy cục bộ + bản triển khai Vercel của dự án (khớp
# bằng biểu thức chính quy), cộng thêm những gì đặt trong CORS_ORIGINS.
# Chi tiết và lý do vì sao mở sẵn vẫn an toàn: xem backend/config.py.
CORS_ORIGINS, CORS_ORIGIN_REGEX = nguon_cors()

# In ra lúc khởi động. Trước đây quên đặt CORS_ORIGINS là giao diện chết hẳn mà
# chỉ báo "CORS policy" chung chung; giờ mặc định đã đủ chạy, nhưng vẫn in để
# khi dùng tên miền khác thì nhìn log là biết ngay vì sao bị chặn.
print(
    f"CORS cho phép: {', '.join(CORS_ORIGINS)} · khớp mẫu: {CORS_ORIGIN_REGEX}",
    flush=True,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_origin_regex=CORS_ORIGIN_REGEX,
    # Hệ thống xác thực bằng thẻ Bearer trong header, không dùng cookie phiên,
    # nên không cần allow_credentials. Bật cùng allow_origins="*" còn là cấu hình
    # không hợp lệ theo chuẩn CORS và bị trình duyệt từ chối.
    allow_credentials=False,
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

@app.get("/health", tags=["health"])
async def health():
    """Điểm kiểm tra sống cho nền tảng triển khai."""
    return {"status": "ok"}


# Phục vụ giao diện đã build, CHỈ KHI có sẵn trong cùng máy chủ.
#
# Bình thường giao diện được triển khai riêng (Vercel) nên khối này không chạy.
# Trước đây chỗ này mount thẳng thư mục "frontend" — tức là mã nguồn chưa build,
# khiến trang chủ trả về index.html của Vite trỏ tới /src/main.tsx và hỏng hoàn
# toàn trên môi trường thật. Nay chỉ mount đúng thư mục build.
_FRONTEND_DIST = Path(__file__).resolve().parent.parent / "frontend" / "dist"
if _FRONTEND_DIST.is_dir() and (_FRONTEND_DIST / "index.html").exists():
    app.mount("/", StaticFiles(directory=str(_FRONTEND_DIST), html=True), name="frontend")
