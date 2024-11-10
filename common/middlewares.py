from fastapi import Request, Response, FastAPI
from starlette.middleware.base import BaseHTTPMiddleware
from users.models import User

# from jwt import decode, PyJWTError
from jose import JWTError, jwt, ExpiredSignatureError
from common.config import SECRET_KEY, ALGORITHM
from typing import Callable, Awaitable
from fastapi.responses import JSONResponse


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
            # except JWTError as e:
            #     raise HTTPException(
            #         status_code=403, detail=f"Could not validate credentials, msg-{e}"
            #     )
            except ExpiredSignatureError:
                return JSONResponse(
                    status_code=403, content={"detail": "Token has expired"}
                )
            except JWTError as e:
                return JSONResponse(
                    status_code=403,
                    content={"detail": f"Could not validate credentials: {str(e)}"},
                )
            except Exception as e:
                return JSONResponse(
                    status_code=403, content={"detail": f"An error occurred: {str(e)}"}
                )
            # except Exception as e:
            #     raise HTTPException(status_code=403, detail=str(e))
        response = await call_next(request)
        return response


class LimitUploadSizeMiddleware(BaseHTTPMiddleware):
    # 파일 용량 제한 미들웨어 정의
    def __init__(self, app: FastAPI, max_upload_size: int) -> None:
        super().__init__(app)
        self.max_upload_size = max_upload_size

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        content_length = request.headers.get("content-length")
        if content_length:
            if int(content_length) > self.max_upload_size:
                return Response(
                    content="파일 크기가 너무 큽니다.",
                    status_code=413,  # Payload Too Large
                )
        return await call_next(request)
