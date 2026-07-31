"""
Quản lý đơn vị (Công an đơn vị, địa phương).

Theo Hướng dẫn 20-HD/ĐUCA, đối tượng áp dụng gồm các đơn vị: Bộ; Công an tỉnh,
thành phố; Cục; Phòng; Trung đoàn; Đội và tương đương; Công an xã, phường, đặc khu.
Đơn vị là đối tượng của đánh giá KPI tập thể và là phạm vi của Danh mục nhiệm vụ.
"""
import asyncio
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from bson import ObjectId
from typing import List, Optional

from backend.database import db
from backend.security import get_current_user
from backend.dependencies import require_admin
from backend.models.schemas import (
    DepartmentCreate, DepartmentUpdate, DepartmentResponse, DepartmentNode,
)
from backend.services.audit_service import log_action

router = APIRouter()


def fix_id(doc):
    doc["_id"] = str(doc["_id"])
    return doc


@router.get("/tree", response_model=List[DepartmentNode])
async def get_department_tree(
    period_month: Optional[int] = None,
    period_year: Optional[int] = None,
    current_user: dict = Depends(get_current_user),
):
    """
    Cây cơ cấu tổ chức nhiều cấp, kèm số liệu tổng hợp của từng đơn vị:
    số cán bộ, KPI tập thể kỳ gần nhất và phân bố cán bộ theo nhóm xếp loại.
    """
    eval_match: dict = {"overall_status": "approved"}
    if period_year:
        eval_match["period_year"] = period_year
    if period_month:
        eval_match["period_month"] = period_month

    # Tổng hợp bằng aggregation để chỉ chuyển về vài chục dòng thay vì hàng nghìn tài liệu
    departments, member_rows, collective_rows, group_rows = await asyncio.gather(
        db.departments.find({}).sort("name", 1).to_list(500),
        db.users.aggregate([
            {"$match": {"role": {"$ne": "admin"}, "department_id": {"$ne": None}}},
            {"$group": {"_id": "$department_id", "n": {"$sum": 1}}},
        ]).to_list(500),
        db.kpi_evaluations.aggregate([
            {"$match": {**eval_match, "evaluation_type": "collective"}},
            {"$sort": {"period_year": -1, "period_month": -1}},
            {"$group": {
                "_id": "$department_id",
                "kpi": {"$first": "$approval.kpi_score"},
                "grp": {"$first": "$approval.kpi_group"},
            }},
        ]).to_list(500),
        db.kpi_evaluations.aggregate([
            {"$match": {**eval_match, "evaluation_type": "individual"}},
            {"$group": {
                "_id": {"d": "$department_id", "g": "$approval.kpi_group"},
                "n": {"$sum": 1},
            }},
        ]).to_list(2000),
    )

    member_count = {r["_id"]: r["n"] for r in member_rows}
    latest_collective = {r["_id"]: (r.get("kpi"), r.get("grp")) for r in collective_rows}

    group_stats: dict = {}
    for r in group_rows:
        did, grp = r["_id"].get("d"), r["_id"].get("g")
        if not did or grp not in ("group_1", "group_2", "group_3"):
            continue
        group_stats.setdefault(did, {"group_1": 0, "group_2": 0, "group_3": 0})[grp] += r["n"]

    nodes: dict = {}
    for d in departments:
        did = str(d["_id"])
        collective = latest_collective.get(did)
        nodes[did] = {
            **fix_id(dict(d)),
            "children": [],
            "member_count": member_count.get(did, 0),
            "total_member_count": member_count.get(did, 0),
            "collective_kpi": collective[0] if collective else None,
            "collective_kpi_group": collective[1] if collective else None,
            "group_stats": group_stats.get(did, {"group_1": 0, "group_2": 0, "group_3": 0}),
        }

    # Ghép cây theo parent_id
    roots = []
    for did, node in nodes.items():
        parent_id = node.get("parent_id")
        if parent_id and parent_id in nodes:
            nodes[parent_id]["children"].append(node)
        else:
            roots.append(node)

    # Cộng dồn số cán bộ từ dưới lên
    def rollup(node) -> int:
        total = node["member_count"] + sum(rollup(c) for c in node["children"])
        node["total_member_count"] = total
        return total

    for r in roots:
        rollup(r)

    return roots


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


@router.get("/{department_id}/members")
async def get_department_members(
    department_id: str,
    period_month: Optional[int] = None,
    period_year: Optional[int] = None,
    current_user: dict = Depends(get_current_user),
):
    """
    Danh sách cán bộ của đơn vị kèm tải việc và KPI, tính bằng aggregation
    trong một lượt truy vấn thay vì gọi hồ sơ từng người.
    """
    now = datetime.utcnow()
    month = period_month or now.month
    year = period_year or now.year

    users, task_rows, kpi_rows = await asyncio.gather(
        db.users.find({"department_id": department_id, "role": {"$ne": "admin"}}).to_list(500),
        db.tasks.aggregate([
            {"$match": {"department_id": department_id, "period_month": month, "period_year": year}},
            {"$group": {
                "_id": "$assigned_to",
                "tasks_assigned": {"$sum": 1},
                "tasks_completed": {
                    "$sum": {"$cond": [{"$eq": ["$status", "done"]}, 1, 0]}
                },
                "tasks_overdue": {
                    "$sum": {"$cond": [
                        {"$and": [{"$ne": ["$status", "done"]}, {"$lt": ["$deadline", now]}]}, 1, 0
                    ]}
                },
                "open_points": {
                    "$sum": {"$cond": [
                        {"$ne": ["$status", "done"]},
                        {"$multiply": ["$kpi_point", {"$ifNull": ["$quantity_assigned", 1]}]},
                        0,
                    ]}
                },
                "classified_tasks": {
                    "$sum": {"$cond": [{"$ne": ["$classification", "thuong"]}, 1, 0]}
                },
                "total_revisions": {"$sum": {"$ifNull": ["$revision_count", 0]}},
                "total_reminders": {"$sum": {"$ifNull": ["$reminder_count", 0]}},
            }},
        ]).to_list(500),
        db.kpi_evaluations.aggregate([
            {"$match": {
                "department_id": department_id,
                "evaluation_type": "individual",
                "period_type": "monthly",
                "overall_status": "approved",
                "period_year": year,
            }},
            {"$sort": {"period_month": -1}},
            {"$group": {
                "_id": "$target_id",
                "latest_kpi": {"$first": "$approval.kpi_score"},
                "latest_kpi_group": {"$first": "$approval.kpi_group"},
                "avg_kpi": {"$avg": "$approval.kpi_score"},
                "months": {"$sum": 1},
            }},
        ]).to_list(500),
    )

    stats = {r["_id"]: r for r in task_rows}
    kpis = {r["_id"]: r for r in kpi_rows}

    from backend.routers.employees import workload_status

    members = []
    for u in users:
        uid = str(u["_id"])
        s = stats.get(uid, {})
        k = kpis.get(uid, {})
        capacity = int(u.get("capacity_points", 300) or 300)
        open_points = s.get("open_points", 0) or 0
        percent = round(open_points / capacity * 100, 1) if capacity else 0.0

        members.append({
            "id": uid,
            "name": u.get("name", ""),
            "role": u.get("role", "staff"),
            "position": u.get("position"),
            "rank": u.get("rank"),
            "clearance_level": int(u.get("clearance_level", 0) or 0),
            "capacity_points": capacity,
            "open_points": open_points,
            "workload_percent": percent,
            "workload_status": workload_status(percent).value,
            "tasks_assigned": s.get("tasks_assigned", 0),
            "tasks_completed": s.get("tasks_completed", 0),
            "tasks_overdue": s.get("tasks_overdue", 0),
            "classified_tasks": s.get("classified_tasks", 0),
            "total_revisions": s.get("total_revisions", 0),
            "total_reminders": s.get("total_reminders", 0),
            "latest_kpi": k.get("latest_kpi"),
            "latest_kpi_group": k.get("latest_kpi_group"),
            "yearly_avg_kpi": round(k["avg_kpi"], 2) if k.get("avg_kpi") is not None else None,
        })

    # Lãnh đạo lên trước, sau đó xếp theo tải việc giảm dần
    role_order = {"director": 0, "leader": 1, "staff": 2}
    members.sort(key=lambda m: (role_order.get(m["role"], 3), -m["workload_percent"]))
    return members


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
