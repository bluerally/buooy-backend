# Dockerfile
FROM python:3.12

WORKDIR /app

COPY pyproject.toml poetry.lock* /app/
RUN pip install poetry && poetry config virtualenvs.create false && poetry install --no-dev

COPY . /app

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
# 환경 변수 로깅 및 애플리케이션 시작
#CMD echo "DB_HOST: $DB_HOST" && \
#    echo "DB_PORT: $DB_PORT" && \
#    uvicorn main:app --host 0.0.0.0 --port 8080
