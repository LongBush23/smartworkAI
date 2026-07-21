from fastapi import APIRouter, Depends, HTTPException
from backend.database import db
from backend.security import get_current_user
from backend.models.schemas import CommentCreate, CommentResponse
from bson import ObjectId
from datetime import datetime
from typing import List

router = APIRouter()

def fix_id(doc):
    doc["_id"] = str(doc["_id"])
    return doc

@router.get("/{task_id}/comments", response_model=List[CommentResponse])
async def get_task_comments(task_id: str, current_user: dict = Depends(get_current_user)):
    """Lấy danh sách bình luận của một Task."""
    cursor = db.comments.find({"task_id": task_id}).sort("created_at", 1)
    comments = await cursor.to_list(length=100)
    return [fix_id(c) for c in comments]

@router.post("/{task_id}/comments", response_model=CommentResponse)
async def add_comment(task_id: str, comment: CommentCreate, current_user: dict = Depends(get_current_user)):
    """Thêm bình luận mới vào Task."""
    # Kiểm tra task tồn tại
    task = await db.tasks.find_one({"_id": ObjectId(task_id)})
    if not task:
        raise HTTPException(status_code=404, detail="Không tìm thấy Task")

    new_comment = {
        "task_id": task_id,
        "content": comment.content,
        "user_id": current_user["_id"],
        "user_name": current_user.get("name", "Unknown"),
        "created_at": datetime.utcnow()
    }
    result = await db.comments.insert_one(new_comment)
    new_comment["_id"] = str(result.inserted_id)
    
    # Audit log (tuỳ chọn)
    from backend.services.audit_service import log_action
    await log_action(current_user["_id"], current_user.get("name", ""), "comment.added", "task", task_id, f"Comment ID: {result.inserted_id}")

    return new_comment

@router.delete("/comments/{comment_id}")
async def delete_comment(comment_id: str, current_user: dict = Depends(get_current_user)):
    """Xoá bình luận (Chỉ tác giả hoặc Director+ mới được xoá)"""
    comment = await db.comments.find_one({"_id": ObjectId(comment_id)})
    if not comment:
        raise HTTPException(status_code=404, detail="Không tìm thấy bình luận")

    is_author = comment["user_id"] == current_user["_id"]
    is_director_plus = current_user.get("role") in ["director", "admin"]

    if not is_author and not is_director_plus:
        raise HTTPException(status_code=403, detail="Không có quyền xoá bình luận này")

    await db.comments.delete_one({"_id": ObjectId(comment_id)})
    
    from backend.services.audit_service import log_action
    await log_action(current_user["_id"], current_user.get("name", ""), "comment.deleted", "task", comment["task_id"], f"Comment ID: {comment_id}")

    return {"message": "Đã xoá bình luận"}
