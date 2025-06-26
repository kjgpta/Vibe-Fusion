# Use the official slim Python image
FROM python:3.9-slim

# Install system dependencies for building Python wheels
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        build-essential \
        python3-dev \
        curl && \
    rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy and install Python dependencies
COPY requirements.txt . 
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# (Optional) Expose the port your app listens on
EXPOSE 8501

# Start your app
CMD ["python", "run.py"]
