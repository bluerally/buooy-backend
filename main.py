import uvicorn
from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
from fastapi.templating import Jinja2Templates
from starlette.requests import Request
from users.routers import user_router
from common.config import TORTOISE_ORM
from tortoise import Tortoise
from common.middlewares import AuthMiddleware
from contextlib import asynccontextmanager
# from tortoise.contrib.fastapi import register_tortoise


@asynccontextmanager
async def lifespan(application: FastAPI):
    await Tortoise.init(config=TORTOISE_ORM, timezone="Asia/Seoul")
    await Tortoise.init(config=TORTOISE_ORM)
    yield
    await Tortoise.close_connections()


app = FastAPI(lifespan=lifespan)
# app = FastAPI()
# register_tortoise(
#     app,
#     config=TORTOISE_ORM,
#     generate_schemas=False,  # 필요에 따라 True로 설정
#     add_exception_handlers=True,
# )

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


@app.get("/")
async def health_check():
    return "Health Check Succeed!"


@app.get("/test")
async def test_endpoint(request: Request):
    print(request)
    return "Hello Test!"


@app.get("/home")
async def test_auth(request: Request):
    return templates.TemplateResponse(name="index.html", context={"request": request})


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
