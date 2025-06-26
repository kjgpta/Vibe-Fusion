# Use the official slim Python image
FROM python:3.9-slim

# Install system dependencies for building Python wheels
RUN apt-get update \
 && apt-get install -y --no-install-recommends \
      build-essential \        # gcc, g++ and make
      python3-dev \            # Python C headers
      curl \
 && rm -rf /var/lib/apt/lists/*

# Create app directory
WORKDIR /app

# Copy requirements first (so Docker caches installs)
COPY requirements.txt .

# Upgrade pip then install Python deps (including spaCy & blis)
RUN pip install --no-cache-dir --upgrade pip \
 && pip install --no-cache-dir -r requirements.txt

# Copy the rest of your code
COPY . .

CMD ["python", "run.py"]
