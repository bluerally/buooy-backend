from fastapi import Request, HTTPException, Response
from starlette.middleware.base import BaseHTTPMiddleware
from users.models import User

# from jwt import decode, PyJWTError
from jose import JWTError, jwt
from common.config import SECRET_KEY, ALGORITHM
from typing import Callable, Awaitable


class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        token = request.headers.get("Authorization")
        request.state.user = None
        if token and token.startswith("Bearer "):
            try:
                token = token.split(" ")[1]
                payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
                user_id = payload.get("user_id")
                if user_id:
                    request.state.user = await User.get_or_none(id=user_id)
            # except PyJWTError as e:
            except JWTError as e:
                raise HTTPException(
                    status_code=403, detail=f"Could not validate credentials, msg-{e}"
                )
            except Exception as e:
                raise HTTPException(status_code=403, detail=str(e))
        response = await call_next(request)
        return response
