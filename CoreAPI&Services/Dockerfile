FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# System deps for uvicorn[standard] (uvloop/httptools wheels exist for linux)
RUN pip install --no-cache-dir --upgrade pip

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY app /app/app

# Default runtime env (can be overridden)
ENV HOST=0.0.0.0 \
    PORT=3001 \
    APP_ENV=production \
    LOG_LEVEL=INFO

EXPOSE 3001

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "3001", "--workers", "1"]
