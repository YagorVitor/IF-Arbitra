FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY backend/pyproject.toml backend/constraints.txt ./
COPY backend/app ./app
RUN pip install --no-cache-dir -c constraints.txt . && useradd --uid 10001 --create-home app
COPY backend/alembic.ini ./
COPY backend/migrations ./migrations
USER app
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/ready',timeout=3)"
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2", "--no-proxy-headers", "--timeout-keep-alive", "5"]
