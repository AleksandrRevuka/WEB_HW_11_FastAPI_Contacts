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
        """
        The __call__ function is a decorator that allows us to use the class as a function.
        It takes in the request and current_user, which are passed by FastAPI automatically.
        The __call__ function then checks if the user's role is allowed for this endpoint.

        :param self: Access the class attributes
        :param request: Request: Access the request object
        :param current_user: User: Get the current user
        :param : Check if the user has permission to access the route
        :return: A function that takes a request and current_user as arguments
        """
        if current_user.roles not in self.allowed_roles:
            raise HTTPException(status.HTTP_403_FORBIDDEN, detail="Operations forbidden")
