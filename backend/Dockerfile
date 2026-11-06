FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

WORKDIR /app
COPY backend/requirements.txt backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt
COPY backend backend
COPY scripts scripts

EXPOSE 5000
CMD ["sh", "-c", "python -m backend.db_init && gunicorn --bind 0.0.0.0:5000 --workers 2 --timeout 60 backend.app:app"]