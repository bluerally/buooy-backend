from fastapi import Request, HTTPException
from typing import Callable, TypeVar

# TypeVar 생성
T = TypeVar("T")


# 로그인 필요 데코레이터
def login_required(endpoint_func: Callable[..., T]) -> Callable[..., T]:
    async def wrapper(*args, **kwargs) -> T:
        request = None
        for arg in args:
            if isinstance(arg, Request):
                request = arg
                break

        if request is None:
            raise HTTPException(status_code=400, detail="Request object not found")

        if request.state.user is None:
            raise HTTPException(status_code=401, detail="Not authenticated")

        return await endpoint_func(*args, **kwargs)

    return wrapper
