FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY backend/src/ ./src/
COPY backend/scripts/ ./scripts/

# Create logs directory
RUN mkdir -p logs

# Expose port (Railway sets $PORT)
EXPOSE 8000

# Run the application (use $PORT from Railway)
CMD ["sh", "-c", "python -m uvicorn src.main:app --host 0.0.0.0 --port ${PORT:-8000}"]