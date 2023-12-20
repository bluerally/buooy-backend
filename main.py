from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, Depends
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.templating import Jinja2Templates
from starlette.middleware.cors import CORSMiddleware
from starlette.requests import Request
from tortoise import Tortoise

from common.config import TORTOISE_ORM
from common.middlewares import AuthMiddleware
from users.routers import user_router
from common.dependencies import get_admin


@asynccontextmanager
async def lifespan(application: FastAPI):
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
    "http://www.bluerally.net",
    "http://localhost:3000",
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


# Swagger UI 권한 설정
@app.get("/docs", include_in_schema=False)
async def get_documentation(admin: str = Depends(get_admin)):
    return get_swagger_ui_html(openapi_url="/openapi.json", title="docs")


@app.get("/openapi.json", include_in_schema=False)
async def openapi(admin: str = Depends(get_admin)):
    return app.openapi()


@app.get("/")
async def health_check():
    return "Health Check Succeed!"


@app.get("/home")
async def test_auth(request: Request):
    return templates.TemplateResponse(name="index.html", context={"request": request})


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
