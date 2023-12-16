from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from users.models import User
from jwt import decode, PyJWTError
from common.config import SECRET_KEY, ALGORITHM


class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        token = request.headers.get("Authorization")
        request.state.user = None
        if token:
            try:
                payload = decode(token, SECRET_KEY, algorithms=[ALGORITHM])
                user_id = payload.get("sub")
                if user_id:
                    request.state.user = await User.get_or_none(id=user_id)
            except PyJWTError:
                raise HTTPException(
                    status_code=403, detail="Could not validate credentials"
                )
        response = await call_next(request)
        return response
