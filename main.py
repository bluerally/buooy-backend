from contextlib import asynccontextmanager
from typing import Any, AsyncIterator, Literal

import uvicorn
from fastapi import FastAPI, Depends, APIRouter
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.templating import Jinja2Templates
from starlette.middleware.cors import CORSMiddleware
from starlette.responses import HTMLResponse
from tortoise import Tortoise
from fastapi.openapi.utils import get_openapi

from admin.routers import admin_router
from common.config import TORTOISE_ORM
from common.dependencies import get_admin
from common.middlewares import AuthMiddleware, LimitUploadSizeMiddleware
from notifications.routers import notification_router
from parties.routers import party_router
from users.routers import user_router
from common.logging_configs import LoggingAPIRoute
from feedback.routers import feedback_router
from common.scheduler import scheduler


@asynccontextmanager
async def lifespan(application: FastAPI) -> AsyncIterator[None]:
    await Tortoise.init(config=TORTOISE_ORM, timezone="Asia/Seoul")
    # start_scheduler()
    yield
    scheduler.shutdown()
    await Tortoise.close_connections()


app = FastAPI(lifespan=lifespan, docs_url=None)


templates = Jinja2Templates(directory="templates")

origins = [
    # "http://127.0.0.1:8000",
    # "http://127.0.0.1:8080",
    # "http://127.0.0.1:80",
    # "https://www.bluerally.net",
    "http://localhost:3000",
    "https://bluerally-fe.vercel.app",
    # "*"
]

# Middleware
app.add_middleware(
    LimitUploadSizeMiddleware,
    max_upload_size=10 * 1024 * 1024,  # 10MB
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(AuthMiddleware)

test_router = APIRouter(
    prefix="/api/test",
    route_class=LoggingAPIRoute,
)

# router include
app.include_router(user_router)
app.include_router(party_router)
app.include_router(feedback_router)
app.include_router(notification_router)
app.include_router(admin_router)


# Swagger UI 권한 설정

Json = dict[str | Literal["anyOf", "type"], "Json"] | list["Json"] | str | bool


def convert_3_1_to_3_0(json: dict[str, Json]) -> dict[str, Json]:
    """OpenAPI 3.1.0을 3.0.2로 변환"""
    json["openapi"] = "3.0.2"

    def inner(yaml_dict: Json) -> None:
        if isinstance(yaml_dict, dict):
            if "anyOf" in yaml_dict and isinstance((anyOf := yaml_dict["anyOf"]), list):
                for i, item in enumerate(anyOf):
                    if isinstance(item, dict) and item.get("type") == "null":
                        anyOf.pop(i)
                        yaml_dict["nullable"] = True
            if "examples" in yaml_dict:
                examples = yaml_dict["examples"]
                del yaml_dict["examples"]
                if isinstance(examples, list) and len(examples):
                    yaml_dict["example"] = examples[0]
            for value in yaml_dict.values():
                inner(value)
        elif isinstance(yaml_dict, list):
            for item in yaml_dict:
                inner(item)

    inner(json)
    return json


def custom_openapi() -> Any:
    if app.openapi_schema:
        return app.openapi_schema

    # OpenAPI 스키마를 직접 생성
    openapi_schema = get_openapi(
        title="Your API",
        version="1.0.0",
        description="Your API description",
        routes=app.routes,
        openapi_version="3.0.2",  # 버전을 명시적으로 지정
    )

    # 스키마 변환 적용
    converted = convert_3_1_to_3_0(openapi_schema)
    app.openapi_schema = converted

    return converted


# app의 openapi 함수를 교체
app.openapi = custom_openapi
app.openapi_version = "3.0.2"


@app.get("/api/docs", include_in_schema=False)
async def get_documentation(admin: str = Depends(get_admin)) -> HTMLResponse:
    return get_swagger_ui_html(openapi_url="/api/openapi.json", title="docs")


@app.get("/api/openapi.json", include_in_schema=False)
async def openapi(admin: str = Depends(get_admin)) -> Any:
    return app.openapi()


# @app.get("/")
# async def health_check() -> str:
#     return "Health Check Succeed!"


@app.get("/api/health")
async def api_health_check() -> str:
    return "API Health Check Succeed!"


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
