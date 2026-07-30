FROM node:22-bookworm-slim AS frontend-build

WORKDIR /frontend

COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci

COPY frontend ./
RUN npm run build

FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8000

WORKDIR /app

COPY requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY fastapi_app ./fastapi_app
COPY asgi.py ./asgi.py
COPY --from=frontend-build /app/static/frontend ./app/static/frontend

EXPOSE 8000

CMD ["sh", "-c", "uvicorn asgi:app --host 0.0.0.0 --port ${PORT:-8000}"]
