from fastapi import APIRouter, Depends, HTTPException
from backend.database import db
from backend.security import get_current_user
from backend.dependencies import require_leader_or_above
from backend.models.schemas import TaskCreate, TaskUpdate, TaskResponse, NotificationType
from backend.services.notification_service import send_notification
from backend.services.audit_service import log_action
from bson import ObjectId
from typing import List, Optional

router = APIRouter()

def fix_id(doc):
    doc["_id"] = str(doc["_id"])
    return doc

@router.get("/", response_model=List[TaskResponse])
async def get_tasks(
    project_id: Optional[str] = None,
    assignee_id: Optional[str] = None,
    status: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    match_query = {}
    if project_id:
        match_query["project_id"] = project_id
    if assignee_id:
        match_query["assigned_to"] = assignee_id
    if status:
        match_query["status"] = status

    pipeline = [
        {"$match": match_query},
        # Join Project to get project_name
        {
            "$lookup": {
                "from": "projects",
                "let": {"pid": {"$toObjectId": "$project_id"}},
                "pipeline": [
                    {"$match": {"$expr": {"$eq": ["$_id", "$$pid"]}}}
                ],
                "as": "project_info"
            }
        },
        # Join User to get assignee_name
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
        {"$unwind": {"path": "$project_info", "preserveNullAndEmptyArrays": True}},
        {"$unwind": {"path": "$assignee_info", "preserveNullAndEmptyArrays": True}},
        {"$addFields": {
            "project_name": "$project_info.name",
            "assignee_name": "$assignee_info.name"
        }},
        {"$project": {"project_info": 0, "assignee_info": 0}},
        {"$sort": {"deadline": 1}},
    ]
    
    cursor = db.tasks.aggregate(pipeline)
    tasks = await cursor.to_list(length=200)
    return [fix_id(t) for t in tasks]

@router.post("/", response_model=TaskResponse)
async def create_task(task: TaskCreate, current_user: dict = Depends(require_leader_or_above)):
    """Only Leader+ can create tasks."""
    task_dict = task.model_dump(exclude_unset=True, by_alias=True)
    if "_id" in task_dict:
        del task_dict["_id"]
    result = await db.tasks.insert_one(task_dict)
    task_dict["_id"] = str(result.inserted_id)

    # If task is assigned to someone, notify them
    if task.assigned_to:
        await send_notification(
            user_id=task.assigned_to,
            notification_type=NotificationType.TASK_ASSIGNED,
            title="Bạn được gán công việc mới 📋",
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
        raise HTTPException(status_code=404, detail="Không tìm thấy công việc")

    user_role = current_user.get("role", "staff")
    user_level = ROLE_HIERARCHY.get(user_role, 0)

    # Staff can only update tasks assigned to them
    if user_level < ROLE_HIERARCHY["leader"]:
        if existing_task.get("assigned_to") != current_user["_id"]:
            raise HTTPException(status_code=403, detail="Bạn chỉ có thể cập nhật công việc được giao cho mình")

    update_data = task.model_dump(exclude_unset=True, by_alias=True)
    if "_id" in update_data:
        del update_data["_id"]

    # Detect assignment change → notify
    old_assignee = existing_task.get("assigned_to")
    new_assignee = update_data.get("assigned_to")
    if new_assignee and new_assignee != old_assignee:
        await send_notification(
            user_id=new_assignee,
            notification_type=NotificationType.TASK_ASSIGNED,
            title="Bạn được gán công việc mới 📋",
            message=f"\"{existing_task.get('title')}\" đã được gán cho bạn bởi {current_user.get('name', '')}.",
            reference_id=task_id,
            reference_type="task",
        )
        if old_assignee:
            await send_notification(
                user_id=old_assignee,
                notification_type=NotificationType.TASK_UNASSIGNED,
                title="Bạn đã được gỡ khỏi công việc",
                message=f"Bạn không còn phụ trách \"{existing_task.get('title')}\".",
                reference_id=task_id,
                reference_type="task",
            )

    await db.tasks.update_one({"_id": ObjectId(task_id)}, {"$set": update_data})
    await log_action(current_user["_id"], current_user.get("name", ""), "task.updated", "task", task_id, f"Fields: {list(update_data.keys())}")
    return {"message": "Task updated successfully"}

@router.delete("/{task_id}")
async def delete_task(task_id: str, current_user: dict = Depends(require_leader_or_above)):
    """Only Leader+ can delete tasks."""
    await db.tasks.delete_one({"_id": ObjectId(task_id)})
    await db.task_requests.delete_many({"task_id": task_id})
    await log_action(current_user["_id"], current_user.get("name", ""), "task.deleted", "task", task_id)
    return {"message": "Task deleted successfully"}
