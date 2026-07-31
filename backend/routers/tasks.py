from fastapi import APIRouter, Depends, HTTPException
from backend.database import db
from backend.security import get_current_user
from backend.dependencies import require_leader_or_above
from backend.models.schemas import TaskCreate, TaskUpdate, TaskResponse, NotificationType
from backend.models.security_policy import (
    redact, can_access, assert_no_classified_content, rank_of, CLASSIFICATION_LABELS,
)
from backend.services.notification_service import send_notification
from backend.services.audit_service import log_action
from bson import ObjectId
from datetime import datetime
from typing import List, Optional

router = APIRouter()

# Giá trị trạng thái của dữ liệu cũ → trạng thái hiện hành.
# Chuẩn hoá khi đọc để bản ghi cũ vẫn hiển thị được, không cần sửa dữ liệu.
_LEGACY_STATUS = {
    "todo": "assigned",
    "doing": "in_progress",
    "pending": "assigned",
}

# Sản phẩm công việc của dữ liệu cũ (trước đây lưu tên tiếng Việt tự do)
_VALID_PRODUCTS = {
    "cong_van", "bao_cao", "to_trinh", "thong_tu",
    "quy_dinh", "ke_hoach", "de_an", "khac",
}


def fix_id(doc):
    doc["_id"] = str(doc["_id"])

    status = doc.get("status")
    if status in _LEGACY_STATUS:
        doc["status"] = _LEGACY_STATUS[status]

    if doc.get("product") not in _VALID_PRODUCTS:
        doc["product"] = "khac"

    return doc


async def next_task_code(period_year: int, period_month: int) -> str:
    """Sinh mã hiệu nhiệm vụ dạng NV-2026-07-0042 theo từng kỳ."""
    prefix = f"NV-{period_year}-{period_month:02d}-"
    count = await db.tasks.count_documents({"code": {"$regex": f"^{prefix}"}})
    return f"{prefix}{count + 1:04d}"

@router.get("/", response_model=List[TaskResponse])
async def get_tasks(
    assignee_id: Optional[str] = None,
    department_id: Optional[str] = None,
    status: Optional[str] = None,
    task_type: Optional[str] = None,
    classification: Optional[str] = None,
    period_month: Optional[int] = None,
    period_year: Optional[int] = None,
    current_user: dict = Depends(get_current_user)
):
    """
    Danh sách nhiệm vụ công tác. Cán bộ không giữ chức vụ chỉ thấy nhiệm vụ của mình.

    Nhiệm vụ có độ mật vượt cấp độ tiếp cận của người gọi sẽ được lược bỏ các
    trường nhạy cảm NGAY TẠI MÁY CHỦ — không gửi về trình duyệt.
    """
    match_query = {}
    role = current_user.get("role", "staff")

    if assignee_id:
        match_query["assigned_to"] = assignee_id
    elif role == "staff":
        # Cán bộ không giữ chức vụ chỉ thấy nhiệm vụ của mình
        match_query["assigned_to"] = str(current_user["_id"])

    if department_id:
        match_query["department_id"] = department_id
    elif role in ("leader", "director") and current_user.get("department_id"):
        # Lãnh đạo, chỉ huy chỉ theo dõi nhiệm vụ trong đơn vị mình phụ trách
        match_query["department_id"] = current_user["department_id"]
    if status:
        match_query["status"] = status
    if task_type:
        match_query["task_type"] = task_type
    if classification:
        match_query["classification"] = classification
    if period_month:
        match_query["period_month"] = period_month
    if period_year:
        match_query["period_year"] = period_year

    pipeline = [
        {"$match": match_query},
        # Join cán bộ được giao nhiệm vụ
        {
            "$lookup": {
                "from": "users",
                "let": {"uid": "$assigned_to"},
                "pipeline": [
                    {"$match": {"$expr": {"$eq": [{"$toString": "$_id"}, "$$uid"]}}}
                ],
                "as": "assignee_info"
            }
        },
        # Join đơn vị
        {
            "$lookup": {
                "from": "departments",
                "let": {"did": "$department_id"},
                "pipeline": [
                    {"$match": {"$expr": {"$eq": [{"$toString": "$_id"}, "$$did"]}}}
                ],
                "as": "department_info"
            }
        },
        {"$unwind": {"path": "$assignee_info", "preserveNullAndEmptyArrays": True}},
        {"$unwind": {"path": "$department_info", "preserveNullAndEmptyArrays": True}},
        {"$addFields": {
            "assignee_name": "$assignee_info.name",
            "department_name": "$department_info.name"
        }},
        {"$project": {"assignee_info": 0, "department_info": 0}},
        {"$sort": {"deadline": 1}},
    ]

    cursor = db.tasks.aggregate(pipeline)
    tasks = await cursor.to_list(length=500)
    return [redact(fix_id(t), current_user) for t in tasks]


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(task_id: str, current_user: dict = Depends(get_current_user)):
    """Chi tiết một nhiệm vụ. Truy cập nhiệm vụ có độ mật đều được ghi nhật ký."""
    doc = await db.tasks.find_one({"_id": ObjectId(task_id)})
    if not doc:
        raise HTTPException(status_code=404, detail="Không tìm thấy nhiệm vụ công tác")

    fix_id(doc)

    if rank_of(doc.get("classification")) > 0:
        allowed = can_access(current_user, doc)
        await log_action(
            current_user["_id"], current_user.get("name", ""),
            "task.classified_access" if allowed else "task.classified_denied",
            "task", task_id,
            f"Độ mật: {CLASSIFICATION_LABELS.get(doc.get('classification'), '?')}"
            f" · Mã hiệu: {doc.get('code', '-')}",
        )

    return redact(doc, current_user)

@router.post("/", response_model=TaskResponse)
async def create_task(task: TaskCreate, current_user: dict = Depends(require_leader_or_above)):
    """Chỉ lãnh đạo, chỉ huy trở lên được giao nhiệm vụ."""
    task_dict = task.model_dump(exclude_unset=True, by_alias=True)
    task_dict.pop("_id", None)

    # Nhiệm vụ có độ mật không được lưu nội dung tự do trong hệ thống
    assert_no_classified_content(task_dict)

    # Người giao chỉ được giao nhiệm vụ trong phạm vi cấp độ tiếp cận của mình
    if rank_of(task_dict.get("classification")) > int(current_user.get("clearance_level", 0) or 0):
        raise HTTPException(
            status_code=403,
            detail="Bạn không đủ cấp độ tiếp cận để giao nhiệm vụ ở độ mật này",
        )

    now = datetime.utcnow()
    task_dict.setdefault("period_month", now.month)
    task_dict.setdefault("period_year", now.year)
    if not task_dict.get("code"):
        task_dict["code"] = await next_task_code(task_dict["period_year"], task_dict["period_month"])
    task_dict["assigned_by"] = str(current_user["_id"])
    task_dict["assigned_at"] = now

    result = await db.tasks.insert_one(task_dict)
    task_dict["_id"] = str(result.inserted_id)

    # If task is assigned to someone, notify them
    if task.assigned_to:
        await send_notification(
            user_id=task.assigned_to,
            notification_type=NotificationType.TASK_ASSIGNED,
            title="Bạn được giao nhiệm vụ công tác mới 📋",
            message=f"\"{task.title}\" đã được gán cho bạn bởi {current_user.get('name', '')}.",
            reference_id=str(result.inserted_id),
            reference_type="task",
        )

    await log_action(current_user["_id"], current_user.get("name", ""), "task.created", "task", str(result.inserted_id), f"Title: {task.title}")
    return task_dict

@router.put("/{task_id}")
async def update_task(task_id: str, task: TaskUpdate, current_user: dict = Depends(get_current_user)):
    """Staff can update their own tasks; Leader+ can update any task."""
    from backend.dependencies import ROLE_HIERARCHY
    
    existing_task = await db.tasks.find_one({"_id": ObjectId(task_id)})
    if not existing_task:
        raise HTTPException(status_code=404, detail="Không tìm thấy nhiệm vụ công tác")

    user_role = current_user.get("role", "staff")
    user_level = ROLE_HIERARCHY.get(user_role, 0)

    # Staff can only update tasks assigned to them
    if user_level < ROLE_HIERARCHY["leader"]:
        if existing_task.get("assigned_to") != current_user["_id"]:
            raise HTTPException(status_code=403, detail="Bạn chỉ có thể cập nhật nhiệm vụ được giao cho mình")

    update_data = task.model_dump(exclude_unset=True, by_alias=True)
    update_data.pop("_id", None)

    # Kiểm tra theo độ mật SAU khi ghép: tránh lách bằng cách sửa từng trường
    merged = {**existing_task, **update_data}
    assert_no_classified_content(merged)

    if not can_access(current_user, existing_task):
        raise HTTPException(
            status_code=403,
            detail="Bạn không đủ cấp độ tiếp cận để sửa nhiệm vụ này",
        )

    # Detect assignment change → notify
    old_assignee = existing_task.get("assigned_to")
    new_assignee = update_data.get("assigned_to")
    if new_assignee and new_assignee != old_assignee:
        await send_notification(
            user_id=new_assignee,
            notification_type=NotificationType.TASK_ASSIGNED,
            title="Bạn được giao nhiệm vụ công tác mới 📋",
            message=f"\"{existing_task.get('title')}\" đã được gán cho bạn bởi {current_user.get('name', '')}.",
            reference_id=task_id,
            reference_type="task",
        )
        if old_assignee:
            await send_notification(
                user_id=old_assignee,
                notification_type=NotificationType.TASK_UNASSIGNED,
                title="Bạn đã được gỡ khỏi nhiệm vụ công tác",
                message=f"Bạn không còn phụ trách nhiệm vụ \"{existing_task.get('title')}\".",
                reference_id=task_id,
                reference_type="task",
            )

    await db.tasks.update_one({"_id": ObjectId(task_id)}, {"$set": update_data})
    await log_action(current_user["_id"], current_user.get("name", ""), "task.updated", "task", task_id, f"Fields: {list(update_data.keys())}")
    return {"message": "Task updated successfully"}

@router.delete("/{task_id}")
async def delete_task(task_id: str, current_user: dict = Depends(require_leader_or_above)):
    """Chỉ lãnh đạo, chỉ huy trở lên được xoá nhiệm vụ."""
    await db.tasks.delete_one({"_id": ObjectId(task_id)})
    await db.comments.delete_many({"task_id": task_id})
    await log_action(current_user["_id"], current_user.get("name", ""), "task.deleted", "task", task_id)
    return {"message": "Đã xoá nhiệm vụ công tác"}


@router.post("/{task_id}/remind")
async def remind_task(task_id: str, current_user: dict = Depends(require_leader_or_above)):
    """
    Nhắc nhở về tiến độ. Mỗi lần nhắc nhở làm giảm mức điểm tiến độ (C):
    1 lần ≤75%, 2 lần ≤50%, 3 lần ≤25%, từ 4 lần không tính điểm.
    """
    task = await db.tasks.find_one({"_id": ObjectId(task_id)})
    if not task:
        raise HTTPException(status_code=404, detail="Không tìm thấy nhiệm vụ công tác")

    result = await db.tasks.find_one_and_update(
        {"_id": ObjectId(task_id)},
        {"$inc": {"reminder_count": 1}},
        return_document=True,
    )
    count = result.get("reminder_count", 0)

    if task.get("assigned_to"):
        await send_notification(
            user_id=task["assigned_to"],
            notification_type=NotificationType.TASK_REMINDED,
            title=f"Nhắc nhở tiến độ (lần {count}) ⏰",
            message=f"Nhiệm vụ \"{task.get('title')}\" chưa đảm bảo tiến độ. Đây là lần nhắc nhở thứ {count}.",
            reference_id=task_id,
            reference_type="task",
        )

    await log_action(current_user["_id"], current_user.get("name", ""), "task.reminded", "task", task_id, f"Lần thứ {count}")
    return {"message": f"Đã ghi nhận nhắc nhở lần {count}", "reminder_count": count}


@router.post("/{task_id}/request-revision")
async def request_task_revision(task_id: str, current_user: dict = Depends(require_leader_or_above)):
    """
    Yêu cầu hoàn thiện, chỉnh sửa. Mỗi lần sửa làm giảm mức điểm chất lượng (B):
    1 lần ≤75%, 2-4 lần ≤50%, 5-6 lần ≤25%, từ 7 lần không tính điểm.
    """
    task = await db.tasks.find_one({"_id": ObjectId(task_id)})
    if not task:
        raise HTTPException(status_code=404, detail="Không tìm thấy nhiệm vụ công tác")

    result = await db.tasks.find_one_and_update(
        {"_id": ObjectId(task_id)},
        {"$inc": {"revision_count": 1}, "$set": {"status": "review"}},
        return_document=True,
    )
    count = result.get("revision_count", 0)

    if task.get("assigned_to"):
        await send_notification(
            user_id=task["assigned_to"],
            notification_type=NotificationType.TASK_REVISION,
            title=f"Yêu cầu hoàn thiện, chỉnh sửa (lần {count}) 📝",
            message=f"Nhiệm vụ \"{task.get('title')}\" cần hoàn thiện, chỉnh sửa. Đây là lần thứ {count}.",
            reference_id=task_id,
            reference_type="task",
        )

    await log_action(current_user["_id"], current_user.get("name", ""), "task.revision_requested", "task", task_id, f"Lần thứ {count}")
    return {"message": f"Đã ghi nhận yêu cầu chỉnh sửa lần {count}", "revision_count": count}
