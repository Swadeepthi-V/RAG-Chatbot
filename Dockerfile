# Use an official lightweight Python runtime as a parent image
FROM python:3.10-slim

# Set environment variables to prevent Python from writing pyc files and buffering stdout/stderr
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app/src/app

# Set the build working directory
WORKDIR /app

# Install system-level build tools required to compile C++ dependencies (like chromadb's hnswlib)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy dependencies list first to leverage Docker layer caching
COPY requirements.txt .

# Install Python packages
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application source code
COPY . .

# Set the working directory to where main.py and other source scripts are located
WORKDIR /app/src/app

# Expose the port that FastAPI/Uvicorn runs on
EXPOSE 8000

# Start the FastAPI backend server using Uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
