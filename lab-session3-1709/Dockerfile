# Dockerfile
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# (optional) system deps; slim is usually fine for gunicorn
RUN apt-get update && apt-get install -y --no-install-recommends ca-certificates && \
    rm -rf /var/lib/apt/lists/*

# install deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# app code
COPY app.py .

EXPOSE 5000
ENV PORT=5000

# IMPORTANT: WSGI app is `app` inside app.py -> "app:app"
CMD ["gunicorn","--bind","0.0.0.0:5000","--workers","2","--threads","4","--timeout","60","app:app"]
