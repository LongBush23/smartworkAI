"""
Quản lý đơn vị (Công an đơn vị, địa phương).

Theo Hướng dẫn 20-HD/ĐUCA, đối tượng áp dụng gồm các đơn vị: Bộ; Công an tỉnh,
thành phố; Cục; Phòng; Trung đoàn; Đội và tương đương; Công an xã, phường, đặc khu.
Đơn vị là đối tượng của đánh giá KPI tập thể và là phạm vi của Danh mục nhiệm vụ.
"""
from fastapi import APIRouter, Depends, HTTPException
from bson import ObjectId
from typing import List, Optional

from backend.database import db
from backend.security import get_current_user
from backend.dependencies import require_admin
from backend.models.schemas import DepartmentCreate, DepartmentUpdate, DepartmentResponse
from backend.services.audit_service import log_action

router = APIRouter()


def fix_id(doc):
    doc["_id"] = str(doc["_id"])
    return doc


@router.get("/", response_model=List[DepartmentResponse])
async def list_departments(
    force_system: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
):
    """Danh sách đơn vị. Mọi cán bộ đã đăng nhập đều xem được."""
    query = {}
    if force_system:
        query["force_system"] = force_system
    cursor = db.departments.find(query).sort("name", 1)
    departments = await cursor.to_list(length=500)
    return [fix_id(d) for d in departments]


@router.get("/{department_id}", response_model=DepartmentResponse)
async def get_department(department_id: str, current_user: dict = Depends(get_current_user)):
    doc = await db.departments.find_one({"_id": ObjectId(department_id)})
    if not doc:
        raise HTTPException(status_code=404, detail="Không tìm thấy đơn vị")
    return fix_id(doc)


@router.post("/", response_model=DepartmentResponse)
async def create_department(
    department: DepartmentCreate,
    current_user: dict = Depends(require_admin),
):
    """Chỉ quản trị hệ thống được tạo đơn vị."""
    existing = await db.departments.find_one({"name": department.name})
    if existing:
        raise HTTPException(status_code=400, detail="Tên đơn vị đã tồn tại")

    doc = department.model_dump()
    result = await db.departments.insert_one(doc)
    doc["_id"] = str(result.inserted_id)

    await log_action(
        current_user["_id"], current_user.get("name", ""),
        "department.created", "department", doc["_id"], f"Tên: {department.name}",
    )
    return doc


@router.put("/{department_id}")
async def update_department(
    department_id: str,
    department: DepartmentUpdate,
    current_user: dict = Depends(require_admin),
):
    update_data = department.model_dump(exclude_unset=True)
    if not update_data:
        return {"message": "Không có thay đổi"}

    result = await db.departments.update_one(
        {"_id": ObjectId(department_id)}, {"$set": update_data}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Không tìm thấy đơn vị")

    await log_action(
        current_user["_id"], current_user.get("name", ""),
        "department.updated", "department", department_id, f"Trường: {list(update_data.keys())}",
    )
    return {"message": "Đã cập nhật đơn vị"}


@router.delete("/{department_id}")
async def delete_department(department_id: str, current_user: dict = Depends(require_admin)):
    """Không cho xoá đơn vị còn cán bộ để tránh mất liên kết dữ liệu KPI."""
    member_count = await db.users.count_documents({"department_id": department_id})
    if member_count > 0:
        raise HTTPException(
            status_code=400,
            detail=f"Đơn vị còn {member_count} cán bộ, không thể xoá",
        )

    result = await db.departments.delete_one({"_id": ObjectId(department_id)})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Không tìm thấy đơn vị")

    await log_action(
        current_user["_id"], current_user.get("name", ""),
        "department.deleted", "department", department_id,
    )
    return {"message": "Đã xoá đơn vị"}
