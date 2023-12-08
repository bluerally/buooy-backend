import uvicorn
from fastapi import FastAPI
from common.config import DB_CONFIG, IS_PRODUCTION
from tortoise.contrib.fastapi import register_tortoise
from starlette.middleware.cors import CORSMiddleware
from users.routers import user_router


app = FastAPI()


origins = [
    "http://127.0.0.1:8000",
]

# Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# router include
app.include_router(user_router)

# Database Init
register_tortoise(
    app=app,
    config=DB_CONFIG,
    generate_schemas=False if IS_PRODUCTION else True,
    add_exception_handlers=True if IS_PRODUCTION else False,
)


@app.get("/")
async def health_check():
    return "Welcome to Dive Match!"


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
