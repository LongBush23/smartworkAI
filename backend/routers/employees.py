from fastapi import APIRouter, Depends, HTTPException
from backend.database import db
from backend.security import get_current_user
from backend.dependencies import require_director_or_above
from backend.models.schemas import (
    UserCreate, UserUpdate, UserResponse, EmployeeProfile, WorkloadStatusEnum,
)
from backend.models.security_policy import rank_of
from backend.security import get_password_hash
from backend.services.audit_service import log_action
from bson import ObjectId
from datetime import datetime
from typing import List, Optional

router = APIRouter()

def fix_id(doc):
    doc["_id"] = str(doc["_id"])
    return doc


def workload_status(percent: float) -> WorkloadStatusEnum:
    """Tình trạng sẵn sàng nhận nhiệm vụ theo tỷ lệ điểm đang đảm nhận / định mức."""
    if percent < 50:
        return WorkloadStatusEnum.SAN_SANG
    if percent < 85:
        return WorkloadStatusEnum.DANG_LAM
    if percent <= 100:
        return WorkloadStatusEnum.GAN_DAY
    return WorkloadStatusEnum.QUA_TAI


@router.get("/{employee_id}/profile", response_model=EmployeeProfile)
async def get_employee_profile(
    employee_id: str,
    period_month: Optional[int] = None,
    period_year: Optional[int] = None,
    current_user: dict = Depends(get_current_user),
):
    """
    Hồ sơ công tác của một cán bộ trong kỳ: tình trạng tải việc, thống kê
    nhiệm vụ, số lần chỉnh sửa/nhắc nhở và diễn biến điểm KPI.
    """
    user = await db.users.find_one({"_id": ObjectId(employee_id)})
    if not user:
        raise HTTPException(status_code=404, detail="Không tìm thấy cán bộ")

    now = datetime.utcnow()
    month = period_month or now.month
    year = period_year or now.year

    dept_name = None
    if user.get("department_id"):
        dept = await db.departments.find_one({"_id": ObjectId(user["department_id"])})
        dept_name = dept.get("name") if dept else None

    tasks = await db.tasks.find({
        "assigned_to": employee_id,
        "period_month": month,
        "period_year": year,
    }).to_list(500)

    open_points = 0
    points_assigned = 0
    points_completed = 0
    completed = in_progress = overdue = classified = 0

    for t in tasks:
        point = t.get("kpi_point", 0)
        qty = t.get("quantity_assigned", 1) or 1
        assigned_points = point * qty
        points_assigned += assigned_points

        if rank_of(t.get("classification")) > 0:
            classified += 1

        if t.get("status") == "done":
            completed += 1
            points_completed += point * (t.get("quantity_completed", 0) or 0)
        else:
            in_progress += 1
            open_points += assigned_points
            deadline = t.get("deadline")
            if deadline and deadline < now:
                overdue += 1

    capacity = int(user.get("capacity_points", 300) or 300)
    percent = round(open_points / capacity * 100, 1) if capacity else 0.0

    # Diễn biến KPI trong năm
    # Chỉ lấy 3 trường: một bản ghi đầy đủ nặng khoảng 17 KB vì kèm chi tiết
    # từng nhiệm vụ, mà chỗ này chỉ cần vẽ đường diễn biến KPI.
    evaluations = await db.kpi_evaluations.find({
        "target_id": employee_id,
        "evaluation_type": "individual",
        "period_type": "monthly",
        "period_year": year,
        "overall_status": "approved",
    }, {
        "period_month": 1, "approval.kpi_score": 1, "approval.kpi_group": 1,
    }).to_list(24)
    evaluations.sort(key=lambda e: e.get("period_month") or 0)

    history = [
        {
            "period_month": e.get("period_month"),
            "kpi_score": (e.get("approval") or {}).get("kpi_score"),
            "kpi_group": (e.get("approval") or {}).get("kpi_group"),
        }
        for e in evaluations
        if (e.get("approval") or {}).get("kpi_score") is not None
    ]
    scores = [h["kpi_score"] for h in history]

    return {
        "id": str(user["_id"]),
        "name": user.get("name", ""),
        "username": user.get("username", ""),
        "email": user.get("email"),
        "role": user.get("role", "staff"),
        "position": user.get("position"),
        "rank": user.get("rank"),
        "service_number": user.get("service_number"),
        "clearance_level": int(user.get("clearance_level", 0) or 0),
        "department_id": user.get("department_id"),
        "department_name": dept_name,
        "is_commander": user.get("role") in ("leader", "director"),
        "period_month": month,
        "period_year": year,
        "capacity_points": capacity,
        "open_points": open_points,
        "workload_percent": percent,
        "workload_status": workload_status(percent),
        "tasks_assigned": len(tasks),
        "tasks_completed": completed,
        "tasks_in_progress": in_progress,
        "tasks_overdue": overdue,
        "points_assigned": points_assigned,
        "points_completed": points_completed,
        "classified_tasks": classified,
        "total_revisions": sum(t.get("revision_count", 0) for t in tasks),
        "total_reminders": sum(t.get("reminder_count", 0) for t in tasks),
        "latest_kpi": scores[-1] if scores else None,
        "latest_kpi_group": history[-1]["kpi_group"] if history else None,
        "yearly_avg_kpi": round(sum(scores) / len(scores), 2) if scores else None,
        "kpi_history": history,
    }

@router.get("/", response_model=List[UserResponse])
async def get_employees(role: Optional[str] = None, current_user: dict = Depends(get_current_user)):
    """Get employees. Directors see only their department."""
    query = {}
    
    if role:
        query["role"] = role
    else:
        query["role"] = {"$in": ["staff", "leader"]}
    
    # Department scoping for directors
    user_role = current_user.get("role", "staff")
    if user_role == "director" and current_user.get("department_id"):
        query["department_id"] = current_user["department_id"]
    
    cursor = db.users.find(query)
    employees = await cursor.to_list(length=200)
    return [fix_id(e) for e in employees]

@router.post("/", response_model=UserResponse)
async def create_employee(employee: UserCreate, current_user: dict = Depends(require_director_or_above)):
    """Only Director+ can create employees."""
    existing = await db.users.find_one({"username": employee.username})
    if existing:
        raise HTTPException(status_code=400, detail="Username đã tồn tại")
    
    emp_dict = employee.model_dump(exclude_unset=True, by_alias=True)
    if "_id" in emp_dict:
        del emp_dict["_id"]
    
    # Director can only create staff/leader; Admin can create any role
    if current_user.get("role") == "director" and emp_dict.get("role") not in ["staff", "leader", None]:
        raise HTTPException(status_code=403, detail="Lãnh đạo đơn vị chỉ được tạo tài khoản Cán bộ hoặc Lãnh đạo, chỉ huy")
    
    if not emp_dict.get("role"):
        emp_dict["role"] = "staff"
    
    emp_dict["hashed_password"] = get_password_hash(emp_dict.pop("password"))
    emp_dict["is_commander"] = emp_dict.get("role") in ("director", "leader")


    # Auto-assign department from creator if not specified
    if not emp_dict.get("department_id") and current_user.get("department_id"):
        emp_dict["department_id"] = current_user["department_id"]
    
    result = await db.users.insert_one(emp_dict)
    emp_dict["_id"] = str(result.inserted_id)
    
    await log_action(current_user["_id"], current_user.get("name", ""), "employee.created", "user", str(result.inserted_id), f"Name: {employee.name}, Role: {emp_dict.get('role')}")
    return emp_dict

@router.put("/{employee_id}")
async def update_employee(employee_id: str, employee: UserUpdate, current_user: dict = Depends(require_director_or_above)):
    """Only Director+ can update employees."""
    update_data = employee.model_dump(exclude_unset=True, by_alias=True)
    if "_id" in update_data:
        del update_data["_id"]

    # Đổi vai trò thì cập nhật lại cờ lãnh đạo, chỉ huy
    if "role" in update_data:
        update_data["is_commander"] = update_data["role"] in ("director", "leader")

    await db.users.update_one({"_id": ObjectId(employee_id)}, {"$set": update_data})
    
    await log_action(current_user["_id"], current_user.get("name", ""), "employee.updated", "user", employee_id, f"Fields: {list(update_data.keys())}")
    return {"message": "Employee updated successfully"}

@router.delete("/{employee_id}")
async def delete_employee(employee_id: str, current_user: dict = Depends(require_director_or_above)):
    """Only Director+ can delete employees."""
    await db.users.delete_one({"_id": ObjectId(employee_id)})
    await db.tasks.update_many({"assigned_to": employee_id}, {"$set": {"assigned_to": None}})
    
    await log_action(current_user["_id"], current_user.get("name", ""), "employee.deleted", "user", employee_id)
    return {"message": "Employee deleted successfully"}
