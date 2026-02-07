# Base image
FROM python:3.12-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install system dependencies including Node.js and Chromium for Puppeteer
RUN apt-get update && apt-get install -y \
    curl \
    gnupg \
    libgl1 \
    libglib2.0-0 \
    chromium \
    chromium-driver \
    && rm -rf /var/lib/apt/lists/*

# Install Node.js (Version 20)
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --default-timeout=1000 -r requirements.txt

# Install Node.js dependencies (Puppeteer)
COPY package.json .
RUN npm install

# Copy backend application code
COPY app/ ./app/
COPY scripts/ ./scripts/

# Create directory for debug visuals
RUN mkdir -p /app/debug_visuals && chmod 777 /app/debug_visuals

# Expose port
EXPOSE 8000

# Command to run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
