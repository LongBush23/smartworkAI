"""
Task Requests router - handles join requests from staff and approval from directors.
Includes AI auto-approve when match score >= 80%.
"""
from fastapi import APIRouter, Depends, HTTPException
from backend.database import db
from backend.security import get_current_user
from backend.dependencies import require_leader_or_above
from backend.models.schemas import (
    TaskRequestCreate, TaskRequestResponse, TaskRequestReview,
    RequestStatusEnum, NotificationType
)
from backend.services.notification_service import send_notification
from backend.services.audit_service import log_action
from backend.services.gemini_service import get_match_score_from_gemini
from bson import ObjectId
from datetime import datetime
from typing import List, Optional

router = APIRouter()

AUTO_APPROVE_THRESHOLD = 80.0  # AI auto-approves when score >= 80%


def fix_id(doc):
    doc["_id"] = str(doc["_id"])
    return doc


def calculate_match_score(user: dict, task: dict) -> float:
    """
    Calculate AI match score between a user's skills and a task's requirements.
    Returns a score 0-100.
    """
    required_skills = task.get("required_skills", [])
    if not required_skills:
        # No specific skills required → base score from general metrics
        ai_metrics = user.get("ai_metrics", {})
        quality = ai_metrics.get("historical_quality_score", 50)
        on_time = ai_metrics.get("on_time_rate", 0.5) * 100
        return round((quality * 0.6 + on_time * 0.4), 1)

    user_skills = {s["skill_name"].lower(): s.get("self_rating", 3) for s in user.get("skills", [])}

    # Skill matching
    matched = 0
    total_rating = 0
    for rs in required_skills:
        rs_lower = rs.lower()
        if rs_lower in user_skills:
            matched += 1
            total_rating += user_skills[rs_lower]

    if len(required_skills) == 0:
        skill_score = 50
    else:
        coverage = matched / len(required_skills)
        avg_rating = (total_rating / matched * 20) if matched > 0 else 0  # Convert 1-5 to 0-100
        skill_score = coverage * 60 + avg_rating * 0.4

    # Performance bonus
    ai_metrics = user.get("ai_metrics", {})
    quality = ai_metrics.get("historical_quality_score", 50)
    on_time = ai_metrics.get("on_time_rate", 0.5) * 100

    # Workload penalty
    capacity = ai_metrics.get("capacity_hours_per_week", 40)
    current = ai_metrics.get("current_workload_hours", 0)
    workload_ratio = current / capacity if capacity > 0 else 1
    workload_penalty = max(0, (workload_ratio - 0.8) * 50)  # Penalty if > 80% loaded

    final_score = skill_score * 0.5 + quality * 0.25 + on_time * 0.25 - workload_penalty
    return round(max(0, min(100, final_score)), 1)


@router.post("/{task_id}/request-join")
async def request_join_task(task_id: str, data: TaskRequestCreate, current_user: dict = Depends(get_current_user)):
    """Staff submits a request to join a task."""
    # Verify task exists
    task = await db.tasks.find_one({"_id": ObjectId(task_id)})
    if not task:
        raise HTTPException(status_code=404, detail="Không tìm thấy công việc này")

    # Check if already requested
    existing = await db.task_requests.find_one({
        "task_id": task_id,
        "employee_id": current_user["_id"],
        "status": "pending"
    })
    if existing:
        raise HTTPException(status_code=400, detail="Bạn đã gửi yêu cầu cho công việc này rồi")

    # Check if already assigned
    if task.get("assigned_to") == current_user["_id"]:
        raise HTTPException(status_code=400, detail="Bạn đã được gán vào công việc này")

    # Calculate AI match score using Gemini
    gemini_result = await get_match_score_from_gemini(current_user, task)
    match_score = gemini_result["match_score"]
    reasoning = gemini_result["reasoning"]

    request_doc = {
        "task_id": task_id,
        "employee_id": current_user["_id"],
        "employee_name": current_user.get("name", ""),
        "status": RequestStatusEnum.PENDING.value,
        "ai_match_score": match_score,
        "message": data.message or reasoning,
        "created_at": datetime.utcnow(),
        "reviewed_by": None,
        "reviewed_at": None,
        "reject_reason": None,
    }

    # Auto-approve if match score >= threshold
    if match_score >= AUTO_APPROVE_THRESHOLD:
        request_doc["status"] = RequestStatusEnum.AUTO_APPROVED.value
        request_doc["reviewed_at"] = datetime.utcnow()
        request_doc["reviewed_by"] = "AI_AUTO"

        # Assign user to task
        await db.tasks.update_one(
            {"_id": ObjectId(task_id)},
            {"$set": {"assigned_to": current_user["_id"], "status": "in_progress"}}
        )

        # Notify employee
        await send_notification(
            user_id=current_user["_id"],
            notification_type=NotificationType.REQUEST_AUTO_APPROVED,
            title="Yêu cầu được AI tự động duyệt ✅",
            message=f"Yêu cầu tham gia \"{task.get('title')}\" đã được AI tự động duyệt (Match Score: {match_score}%).",
            reference_id=task_id,
            reference_type="task",
        )

        result = await db.task_requests.insert_one(request_doc)
        await log_action(current_user["_id"], current_user.get("name", ""), "task_request.auto_approved", "task_request", str(result.inserted_id), f"Match score: {match_score}%")
        return {"message": f"AI đã tự động duyệt yêu cầu của bạn! (Match Score: {match_score}%)", "status": "auto_approved", "match_score": match_score}

    # Otherwise, save as pending and notify directors
    result = await db.task_requests.insert_one(request_doc)

    # Notify directors/leaders about the pending request
    project = await db.projects.find_one({"_id": ObjectId(task.get("project_id", ""))})
    dept_id = project.get("department_id") if project else None

    # Find directors in the same department
    director_query = {"role": {"$in": ["director", "admin"]}}
    if dept_id:
        director_query["$or"] = [
            {"department_id": dept_id},
            {"role": "admin"}
        ]
    cursor = db.users.find(director_query, {"_id": 1})
    directors = await cursor.to_list(length=50)

    for director in directors:
        await send_notification(
            user_id=str(director["_id"]),
            notification_type=NotificationType.REQUEST_SUBMITTED,
            title="Yêu cầu tham gia mới 📋",
            message=f"{current_user.get('name')} xin tham gia \"{task.get('title')}\" (Match Score: {match_score}%).",
            reference_id=str(result.inserted_id),
            reference_type="task_request",
        )

    await log_action(current_user["_id"], current_user.get("name", ""), "task_request.submitted", "task_request", str(result.inserted_id), f"Task: {task.get('title')}, Score: {match_score}%")
    return {"message": f"Đã gửi yêu cầu thành công (Match Score: {match_score}%). Chờ Quản lý duyệt.", "status": "pending", "match_score": match_score}


@router.get("/requests", response_model=List[TaskRequestResponse])
async def get_pending_requests(
    status: Optional[str] = "pending",
    current_user: dict = Depends(require_leader_or_above)
):
    """Directors/Leaders see pending join requests."""
    query = {}
    if status:
        query["status"] = status

    pipeline = [
        {"$match": query},
        {"$sort": {"created_at": -1}},
        # Join task info
        {
            "$lookup": {
                "from": "tasks",
                "let": {"tid": {"$toObjectId": "$task_id"}},
                "pipeline": [
                    {"$match": {"$expr": {"$eq": ["$_id", "$$tid"]}}}
                ],
                "as": "task_info"
            }
        },
        {"$unwind": {"path": "$task_info", "preserveNullAndEmptyArrays": True}},
        {"$addFields": {
            "task_title": "$task_info.title"
        }},
        {"$project": {"task_info": 0}},
        {"$limit": 100},
    ]

    cursor = db.task_requests.aggregate(pipeline)
    requests = await cursor.to_list(length=100)
    return [fix_id(r) for r in requests]


@router.put("/requests/{request_id}/approve")
async def approve_request(request_id: str, current_user: dict = Depends(require_leader_or_above)):
    """Director/Leader approves a join request."""
    req = await db.task_requests.find_one({"_id": ObjectId(request_id)})
    if not req:
        raise HTTPException(status_code=404, detail="Không tìm thấy yêu cầu")
    if req["status"] != "pending":
        raise HTTPException(status_code=400, detail="Yêu cầu đã được xử lý")

    # Approve the request
    await db.task_requests.update_one(
        {"_id": ObjectId(request_id)},
        {"$set": {
            "status": RequestStatusEnum.APPROVED.value,
            "reviewed_by": current_user["_id"],
            "reviewed_at": datetime.utcnow(),
        }}
    )

    # Assign employee to task
    await db.tasks.update_one(
        {"_id": ObjectId(req["task_id"])},
        {"$set": {"assigned_to": req["employee_id"], "status": "in_progress"}}
    )

    # Notify the employee
    task = await db.tasks.find_one({"_id": ObjectId(req["task_id"])})
    await send_notification(
        user_id=req["employee_id"],
        notification_type=NotificationType.REQUEST_APPROVED,
        title="Yêu cầu được duyệt ✅",
        message=f"Yêu cầu tham gia \"{task.get('title', '')}\" đã được {current_user.get('name')} duyệt.",
        reference_id=req["task_id"],
        reference_type="task",
    )

    await log_action(current_user["_id"], current_user.get("name", ""), "task_request.approved", "task_request", request_id, f"Employee: {req.get('employee_name')}")
    return {"message": "Đã duyệt yêu cầu thành công"}


@router.put("/requests/{request_id}/reject")
async def reject_request(request_id: str, data: TaskRequestReview, current_user: dict = Depends(require_leader_or_above)):
    """Director/Leader rejects a join request."""
    req = await db.task_requests.find_one({"_id": ObjectId(request_id)})
    if not req:
        raise HTTPException(status_code=404, detail="Không tìm thấy yêu cầu")
    if req["status"] != "pending":
        raise HTTPException(status_code=400, detail="Yêu cầu đã được xử lý")

    await db.task_requests.update_one(
        {"_id": ObjectId(request_id)},
        {"$set": {
            "status": RequestStatusEnum.REJECTED.value,
            "reviewed_by": current_user["_id"],
            "reviewed_at": datetime.utcnow(),
            "reject_reason": data.reject_reason,
        }}
    )

    task = await db.tasks.find_one({"_id": ObjectId(req["task_id"])})
    await send_notification(
        user_id=req["employee_id"],
        notification_type=NotificationType.REQUEST_REJECTED,
        title="Yêu cầu bị từ chối ❌",
        message=f"Yêu cầu tham gia \"{task.get('title', '')}\" bị từ chối. Lý do: {data.reject_reason or 'Không có'}.",
        reference_id=req["task_id"],
        reference_type="task",
    )

    await log_action(current_user["_id"], current_user.get("name", ""), "task_request.rejected", "task_request", request_id, f"Reason: {data.reject_reason}")
    return {"message": "Đã từ chối yêu cầu"}
