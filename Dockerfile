# ============================================================
# Dockerfile - FastAPI Backend for Hugging Face Spaces
# ============================================================
# Hugging Face Spaces يشتغل على port 7860 بالـ default
# ============================================================

FROM python:3.11-slim

# Metadata
LABEL maintainer="Smart School FastAPI"

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (for Docker layer caching)
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Copy the entire app
COPY . .

# Create directory for the SQLite database (persistent storage)
RUN mkdir -p /app/data

# Environment variables (يتم override من Hugging Face Secrets)
ENV APP_NAME="Smart School FastAPI"
ENV API_PREFIX="/api"
ENV ALGORITHM="HS256"
ENV ACCESS_TOKEN_EXPIRE_MINUTES=480
ENV SQLSERVER_CONNECTION_STRING="sqlite:///./data/school.db"

# Hugging Face Spaces uses port 7860
EXPOSE 7860

# Run the app
# نستخدم port 7860 عشان Hugging Face Spaces يتطلب كده
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "7860"]
