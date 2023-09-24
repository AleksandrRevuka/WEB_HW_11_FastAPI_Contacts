from typing import List

from fastapi import Depends, HTTPException, Request, status

from src.database.models import Role, User
from src.services.auth import auth_service


class RoleAccess:
    def __init__(self, allowed_roles: List[Role]):
        self.allowed_roles = allowed_roles

    async def __call__(
        self,
        request: Request,
        current_user: User = Depends(auth_service.get_current_user),
    ):
        if current_user.roles not in self.allowed_roles:
            raise HTTPException(
                status.HTTP_403_FORBIDDEN, detail="Operations forbidden"
            )
