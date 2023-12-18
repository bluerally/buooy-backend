import uvicorn
from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
from fastapi.templating import Jinja2Templates
from starlette.requests import Request
from users.routers import user_router
from common.config import SQLITE_DB_URL
from tortoise import Tortoise
from tortoise.contrib.fastapi import register_tortoise
from common.middlewares import AuthMiddleware
from contextlib import asynccontextmanager


@asynccontextmanager
async def lifespan(application: FastAPI):
    await Tortoise.init(db_url=SQLITE_DB_URL, modules={"models": ["users.models"]})
    yield
    await Tortoise.close_connections()


app = FastAPI(lifespan=lifespan)

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


# Database Init
@app.router.lifespan.startup
async def startup_event():
    register_tortoise(
        app,
        db_url="sqlite://:memory:",
        modules={"models": ["your_app.models"]},
        generate_schemas=True,
        add_exception_handlers=True,
    )


@app.router.lifespan.shutdown
async def shutdown_event():
    await Tortoise.close_connections()


@app.get("/")
async def health_check():
    return "Health Check Succeed!"


@app.get("/test")
async def test_endpoint(request: Request):
    print(request)
    return "Hello fuckers!"


@app.get("/home")
async def test_auth(request: Request):
    return templates.TemplateResponse(name="index.html", context={"request": request})


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
