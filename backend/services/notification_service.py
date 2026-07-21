"""
Notification service - creates and stores notifications for users.
"""
from datetime import datetime
from backend.database import db
from backend.models.schemas import NotificationType


async def send_notification(
    user_id: str,
    notification_type: NotificationType,
    title: str,
    message: str,
    reference_id: str = None,
    reference_type: str = None,
):
    """Create a notification for a user."""
    notification = {
        "user_id": user_id,
        "type": notification_type.value,
        "title": title,
        "message": message,
        "reference_id": reference_id,
        "reference_type": reference_type,
        "is_read": False,
        "created_at": datetime.utcnow(),
    }
    await db.notifications.insert_one(notification)


async def send_notification_to_role(
    role: str,
    notification_type: NotificationType,
    title: str,
    message: str,
    reference_id: str = None,
    reference_type: str = None,
    department_id: str = None,
):
    """Send a notification to all users with a specific role (optionally scoped to department)."""
    query = {"role": role}
    if department_id:
        query["department_id"] = department_id

    cursor = db.users.find(query, {"_id": 1})
    users = await cursor.to_list(length=500)

    notifications = []
    for user in users:
        notifications.append({
            "user_id": str(user["_id"]),
            "type": notification_type.value,
            "title": title,
            "message": message,
            "reference_id": reference_id,
            "reference_type": reference_type,
            "is_read": False,
            "created_at": datetime.utcnow(),
        })

    if notifications:
        await db.notifications.insert_many(notifications)
