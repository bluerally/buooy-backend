import uvicorn
from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
from fastapi.templating import Jinja2Templates
from starlette.requests import Request
from users.routers import user_router


app = FastAPI()

templates = Jinja2Templates(directory="templates")

origins = [
    "http://127.0.0.1:8000",
    "http://127.0.0.1:8080",
    "http://127.0.0.1:80",
    "https://www.bluerally.net",
    "http://www.bluerally.net",
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
# TODO 데이터 모델 확정되면 주석 해제
# register_tortoise(
#     app=app,
#     config=DB_CONFIG,
#     generate_schemas=False if IS_PRODUCTION else True,
#     add_exception_handlers=True if IS_PRODUCTION else False,
# )


@app.get("/")
async def health_check():
    return "Health Check Succeed!"


@app.get("/home")
async def test_auth(request: Request):
    return templates.TemplateResponse(name="index.html", context={"request": request})


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
