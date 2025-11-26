FROM python:3.11-slim

WORKDIR /app

# Install PostgreSQL build dependencies and other utilities
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the app
COPY . .

# Create logs directory and set permissions
RUN mkdir -p /app/logs && chmod 755 /app/logs

# Use the clean main script
CMD ["python", "dashboard_metrics_processor.py"]
