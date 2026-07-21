"""
Notifications router - manages user notifications.
"""
from fastapi import APIRouter, Depends
from backend.database import db
from backend.security import get_current_user
from backend.models.schemas import NotificationResponse
from bson import ObjectId
from typing import List

router = APIRouter()


def fix_id(doc):
    doc["_id"] = str(doc["_id"])
    return doc


@router.get("/", response_model=List[NotificationResponse])
async def get_notifications(unread_only: bool = False, current_user: dict = Depends(get_current_user)):
    """Get notifications for the current user."""
    query = {"user_id": current_user["_id"]}
    if unread_only:
        query["is_read"] = False

    cursor = db.notifications.find(query).sort("created_at", -1).limit(50)
    notifications = await cursor.to_list(length=50)
    return [fix_id(n) for n in notifications]


@router.get("/unread-count")
async def get_unread_count(current_user: dict = Depends(get_current_user)):
    """Get count of unread notifications."""
    count = await db.notifications.count_documents({
        "user_id": current_user["_id"],
        "is_read": False,
    })
    return {"count": count}


@router.put("/{notification_id}/read")
async def mark_as_read(notification_id: str, current_user: dict = Depends(get_current_user)):
    """Mark a single notification as read."""
    await db.notifications.update_one(
        {"_id": ObjectId(notification_id), "user_id": current_user["_id"]},
        {"$set": {"is_read": True}},
    )
    return {"message": "Đã đánh dấu đã đọc"}


@router.put("/read-all")
async def mark_all_as_read(current_user: dict = Depends(get_current_user)):
    """Mark all notifications as read."""
    await db.notifications.update_many(
        {"user_id": current_user["_id"], "is_read": False},
        {"$set": {"is_read": True}},
    )
    return {"message": "Đã đánh dấu tất cả là đã đọc"}
