"""
Role-based access control dependencies for SmartWork AI.
Hierarchy: ADMIN > DIRECTOR > LEADER > STAFF
"""
from fastapi import Depends, HTTPException, status
from backend.security import get_current_user

# Role hierarchy (higher number = more privilege)
ROLE_HIERARCHY = {
    "staff": 0,
    "leader": 1,
    "director": 2,
    "admin": 3,
}


def require_role(min_role: str):
    """
    Dependency factory: ensures the current user has at least `min_role` privilege.
    Usage: Depends(require_role("director"))
    """
    min_level = ROLE_HIERARCHY.get(min_role, 0)

    async def role_checker(current_user: dict = Depends(get_current_user)):
        user_role = current_user.get("role", "staff")
        user_level = ROLE_HIERARCHY.get(user_role, 0)
        if user_level < min_level:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Bạn không có quyền thực hiện thao tác này. Yêu cầu vai trò: {min_role}",
            )
        return current_user

    return role_checker


def require_admin(current_user: dict = Depends(get_current_user)):
    """Shortcut: only admin."""
    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Chỉ Admin mới có quyền thực hiện thao tác này.",
        )
    return current_user


def require_director_or_above(current_user: dict = Depends(get_current_user)):
    """Shortcut: director or admin."""
    role = current_user.get("role", "staff")
    if ROLE_HIERARCHY.get(role, 0) < ROLE_HIERARCHY["director"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Chỉ Trưởng phòng (Director) trở lên mới có quyền.",
        )
    return current_user


def require_leader_or_above(current_user: dict = Depends(get_current_user)):
    """Shortcut: leader, director, or admin."""
    role = current_user.get("role", "staff")
    if ROLE_HIERARCHY.get(role, 0) < ROLE_HIERARCHY["leader"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Chỉ Nhóm trưởng (Leader) trở lên mới có quyền.",
        )
    return current_user
