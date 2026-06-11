FROM python:3.11-slim

# psycopg2-binary is self-contained; no system C libs needed
WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Expose the port Railway binds
EXPOSE 8000

# Production: 1 worker (Railway free tier is memory-constrained)
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
