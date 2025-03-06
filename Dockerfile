FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    software-properties-common \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Expose ports for backend and frontend
EXPOSE 8002
EXPOSE 8501

# Create a script to run both services
RUN echo '#!/bin/bash\n\
uvicorn backend.main:app --host 0.0.0.0 --port 8002 & \n\
streamlit run frontend/app.py --server.port=8501 --server.address=0.0.0.0\n\
wait\n' > /app/start.sh && \
    chmod +x /app/start.sh

# Set the entrypoint
ENTRYPOINT ["/app/start.sh"] 