from __future__ import annotations
from fastapi import HTTPException, status

from app.auth import UserInDB
from app.rbac import get_user_permissions

def has_permission(user: UserInDB, perm_code: str) -> bool:
    if user.is_super_admin:
        return True
    perms = get_user_permissions(user.id)
    return perm_code in perms

def require_permission(user: UserInDB, perm_code: str):
    if not has_permission(user, perm_code):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"没有权限：{perm_code}",
        )