# Complete Working MERGE-BOT with ALL Dependencies
FROM python:3.11-slim

# Install system dependencies including ffmpeg
RUN apt-get update && apt-get install -y \
    ffmpeg \
    wget \
    curl \
    git \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first for better Docker layer caching
COPY requirements.txt .

# Install Python dependencies with better error handling
RUN pip3 install --no-cache-dir --upgrade pip setuptools wheel && \
    pip3 install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p downloads logs userdata

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV TZ=Asia/Kolkata

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python3 -c "import sys; import pyrogram; import ffmpeg; sys.exit(0)" || exit 1

# Create enhanced startup script
RUN echo '#!/bin/bash' > /app/start.sh && \
    echo 'echo "[$(date "+%Y-%m-%d %H:%M:%S")] 🚀 Starting Professional MERGE-BOT..."' >> /app/start.sh && \
    echo 'echo "[$(date "+%Y-%m-%d %H:%M:%S")] 📊 Python version: $(python3 --version | cut -d" " -f2)"' >> /app/start.sh && \
    echo 'echo "[$(date "+%Y-%m-%d %H:%M:%S")] 🔍 Checking core dependencies..."' >> /app/start.sh && \
    echo 'python3 -c "import pyrogram, aiohttp, pymongo, PIL, hachoir, psutil, ffmpeg; print(\"[$(date \\\"+%Y-%m-%d %H:%M:%S\\\")] ✅ All core dependencies verified!\")"' >> /app/start.sh && \
    echo 'echo "[$(date "+%Y-%m-%d %H:%M:%S")] 🎬 FFmpeg version: $(ffmpeg -version | head -1)"' >> /app/start.sh && \
    echo 'echo "[$(date "+%Y-%m-%d %H:%M:%S")] 🚀 Launching Professional Merge Bot..."' >> /app/start.sh && \
    echo 'python3 bot.py' >> /app/start.sh && \
    chmod +x /app/start.sh

# Run the application
CMD ["/app/start.sh"]
