FROM python:3.11

WORKDIR /app

# Install system dependencies required by Chromium
RUN apt-get update && apt-get install -y --no-install-recommends \
    chromium \
    xvfb \
    libgtk-3-0 \
    libdbus-glib-1-2 \
    libx11-6 \
    libx11-xcb1 \
    libxcb1 \
    libxss1 \
    libnss3 \
    libnspr4 \
    libxcomposite1 \
    libxcursor1 \
    libxdamage1 \
    libxext6 \
    libxfixes3 \
    libxi6 \
    libxrandr2 \
    libxrender1 \
    libxtst6 \
    fonts-liberation \
    xdg-utils \
    ca-certificates \
    fonts-dejavu-core \
    fonts-freefont-ttf \
    fonts-noto \
    fonts-noto-cjk \
    fonts-noto-color-emoji \
    libpulse0 \
    libasound2 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libatspi2.0-0 \
    libcups2 \
    libdrm2 \
    libgbm1 \
    libglib2.0-0 \
    libpangocairo-1.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Copy and install your Python requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of your application code
COPY . .

# Set environment variables for better browser compatibility
ENV PYTHONUNBUFFERED=1
ENV CHROME_BIN=/usr/bin/chromium

# Command to run your scraper
CMD ["python", "main.py"]