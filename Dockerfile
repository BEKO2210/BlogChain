FROM python:3.11-slim

WORKDIR /app

# Install system dependencies 
RUN apt-get update && apt-get install -y \
    build-essential \
    gcc \
    libc6-dev \
    python3-dev \
    snappy-dev \
    libsnappy-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Set environment variables
ENV FLASK_APP=app.py
ENV FLASK_ENV=production
ENV HOST=0.0.0.0

# Expose port
EXPOSE 5000

# Create data directories
RUN mkdir -p data/users data/blockchain/backups logs

# Set permissions
RUN chmod -R 777 data logs

# Run the application
CMD ["python", "app.py"]
