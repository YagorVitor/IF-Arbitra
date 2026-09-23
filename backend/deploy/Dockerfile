FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 IF_ARBITRA_BACKEND_DIR=/app
WORKDIR /app
COPY backend/pyproject.toml ./
COPY backend/requirements ./requirements
COPY backend/src ./src
RUN pip install --no-cache-dir -c requirements/constraints.txt . && useradd --uid 10001 --create-home app
COPY backend/config ./config
COPY backend/database ./database
USER app
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s CMD python -c "import os,urllib.request; urllib.request.urlopen('http://127.0.0.1:'+os.getenv('PORT','8000')+'/ready',timeout=3)"
CMD ["sh", "-c", "exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --workers 2 --no-proxy-headers --timeout-keep-alive 5"]
