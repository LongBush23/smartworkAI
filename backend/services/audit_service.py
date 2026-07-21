"""
Audit logging service - records all important actions for accountability.
"""
from datetime import datetime
from backend.database import db


async def log_action(
    user_id: str,
    user_name: str,
    action: str,
    target_type: str,
    target_id: str = None,
    details: str = None,
):
    """Record an audit log entry."""
    entry = {
        "user_id": user_id,
        "user_name": user_name,
        "action": action,
        "target_type": target_type,
        "target_id": target_id,
        "details": details,
        "created_at": datetime.utcnow(),
    }
    await db.audit_logs.insert_one(entry)
