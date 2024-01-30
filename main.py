from contextlib import asynccontextmanager
from typing import Any, AsyncIterator

import uvicorn
from fastapi import FastAPI, Depends
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.templating import Jinja2Templates
from starlette.middleware.cors import CORSMiddleware
from starlette.responses import HTMLResponse
from tortoise import Tortoise

from common.config import TORTOISE_ORM
from common.dependencies import get_admin
from common.middlewares import AuthMiddleware
from parties.routers import party_router
from users.routers import user_router


@asynccontextmanager
async def lifespan(application: FastAPI) -> AsyncIterator[None]:
    await Tortoise.init(config=TORTOISE_ORM, timezone="Asia/Seoul")
    yield
    await Tortoise.close_connections()


app = FastAPI(lifespan=lifespan, docs_url=None)


templates = Jinja2Templates(directory="templates")

origins = [
    "http://127.0.0.1:8000",
    "http://127.0.0.1:8080",
    "http://127.0.0.1:80",
    "https://www.bluerally.net",
    "http://localhost:3000",
    "https://localhost:3001",
]

# Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(AuthMiddleware)

# router include
app.include_router(user_router)
app.include_router(party_router)


# Swagger UI 권한 설정
@app.get("/docs", include_in_schema=False)
async def get_documentation(admin: str = Depends(get_admin)) -> HTMLResponse:
    return get_swagger_ui_html(openapi_url="/openapi.json", title="docs")


@app.get("/openapi.json", include_in_schema=False)
async def openapi(admin: str = Depends(get_admin)) -> Any:
    return app.openapi()


@app.get("/")
async def health_check() -> str:
    return "Health Check Succeed!"


# @app.get("/test")
# async def test_api() -> Response:
#     return Response(status_code=201, content={"data": [1, 2, 3, 4]})
# @app.get("/home", response_model=None)
# async def test_auth(request: Request):
#     return templates.TemplateResponse(name="index.html", context={"request": request})


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
