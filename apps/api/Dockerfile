FROM python:3.11-slim

WORKDIR /app

# Copy only the API directory contents (Railway builds with apps/api/ as context
# when rootDirectory is set, OR from repo root when not set)
# This Dockerfile is designed to be built with apps/api/ as the Docker build context.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Cache bust — increment when code changes need to bypass Railway layer cache
ARG CACHEBUST=2
COPY . .

# Railway injects PORT=8080; EXPOSE must match so the edge proxy routes correctly
EXPOSE 8080

CMD ["sh", "-c", "echo 'Starting uvicorn on port '${PORT:-8080} && uvicorn main:app --host 0.0.0.0 --port ${PORT:-8080} --workers 1 --timeout-keep-alive 75 --log-level info"]
