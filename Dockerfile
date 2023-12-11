# Dockerfile
# 사용할 Python 베이스 이미지 지정
FROM python:3.12

# 작업 디렉토리 설정
WORKDIR /app

# 의존성 파일 복사 및 설치
COPY pyproject.toml poetry.lock* /app/
RUN pip install poetry && poetry config virtualenvs.create false && poetry install --no-dev

# 애플리케이션 코드 복사
COPY . /app

# Uvicorn으로 FastAPI 애플리케이션 실행
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
