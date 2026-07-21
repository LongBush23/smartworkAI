from fastapi import APIRouter, Depends, HTTPException
from backend.database import db
from backend.security import get_current_user
from backend.dependencies import require_director_or_above
from backend.models.schemas import UserCreate, UserUpdate, UserResponse
from backend.security import get_password_hash
from backend.services.audit_service import log_action
from bson import ObjectId
from typing import List, Optional

router = APIRouter()

def fix_id(doc):
    doc["_id"] = str(doc["_id"])
    return doc

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
        raise HTTPException(status_code=403, detail="Director chỉ có thể tạo tài khoản Staff hoặc Leader")
    
    if not emp_dict.get("role"):
        emp_dict["role"] = "staff"
    
    emp_dict["hashed_password"] = get_password_hash(emp_dict.pop("password"))
    emp_dict["ai_metrics"] = {
        "historical_quality_score": 50.0,
        "on_time_rate": 1.0,
        "capacity_hours_per_week": 40,
        "current_workload_hours": 0,
    }
    
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
    
    # Convert nested models
    if "skills" in update_data and update_data["skills"]:
        update_data["skills"] = [s.model_dump() if hasattr(s, 'model_dump') else s for s in update_data["skills"]]
    if "preferences" in update_data and update_data["preferences"]:
        update_data["preferences"] = update_data["preferences"].model_dump() if hasattr(update_data["preferences"], 'model_dump') else update_data["preferences"]
    if "ai_metrics" in update_data and update_data["ai_metrics"]:
        update_data["ai_metrics"] = update_data["ai_metrics"].model_dump() if hasattr(update_data["ai_metrics"], 'model_dump') else update_data["ai_metrics"]
    
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
