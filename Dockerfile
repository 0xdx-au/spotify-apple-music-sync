# Multi-stage build: Frontend build stage
FROM node:18-alpine as frontend-build
WORKDIR /app/frontend
COPY web-frontend/package*.json ./
RUN npm ci --only=production
COPY web-frontend/ ./
RUN npm run build

# Backend stage
FROM python:3.11-slim-bullseye

# Security hardening
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd -r appuser && useradd -r -g appuser appuser

# Set working directory
WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ ./src/

# Copy built frontend from frontend-build stage
COPY --from=frontend-build /app/frontend/build ./static/

# Create non-root user and set permissions
RUN chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8000

# Run the application
CMD ["sh", "-c", "uvicorn src.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
