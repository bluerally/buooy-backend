from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from starlette.requests import Request
from users.models import AdminUser
from common.utils import verify_password

security = HTTPBasic()


async def get_current_user(request: Request):
    user = request.state.user
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user


async def get_admin(credentials: Annotated[HTTPBasicCredentials, Depends(security)]):
    user = await AdminUser.get_or_none(username=credentials.username)
    if user and verify_password(credentials.password, user.password):
        return user.username
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Incorrect email or password",
        headers={"WWW-Authenticate": "Basic"},
    )
