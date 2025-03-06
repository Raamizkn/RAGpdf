# Deployment Guide for PDF Research Assistant

This guide provides instructions for deploying the PDF Research Assistant application using Docker and Docker Compose.

## Prerequisites

- [Docker](https://docs.docker.com/get-docker/)
- [Docker Compose](https://docs.docker.com/compose/install/)

## Local Deployment

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/pdf-research-assistant.git
cd pdf-research-assistant
```

### 2. Configure Environment Variables (Optional)

Create a `.env` file in the root directory to override default settings:

```
# API Keys (Optional)
OPENAI_API_KEY=your_api_key_here

# LLM Settings
USE_LOCAL_LLM=true
DEFAULT_LLM_MODEL=mistral

# Docker Configuration
OLLAMA_HOST=ollama
OLLAMA_PORT=11434
```

### 3. Build and Start the Application

```bash
docker-compose up -d
```

This will:
- Build the PDF Research Assistant container
- Start the Ollama container for local LLM support
- Create a network for the containers to communicate
- Mount volumes for data persistence

### 4. Access the Application

- Frontend: http://localhost:8501
- Backend API: http://localhost:8002

### 5. Pull Ollama Models (First Time Setup)

```bash
# Connect to the Ollama container
docker exec -it ollama bash

# Pull the Mistral model
ollama pull mistral

# Exit the container
exit
```

### 6. Stop the Application

```bash
docker-compose down
```

## Cloud Deployment

### Deploying to AWS EC2

1. Launch an EC2 instance with at least 4GB RAM and 2 vCPUs
2. Install Docker and Docker Compose
3. Clone the repository and follow the local deployment steps
4. Configure security groups to allow traffic on ports 8501 and 8002

### Deploying to Google Cloud Run

1. Build the Docker image:
   ```bash
   docker build -t gcr.io/your-project/pdf-research-assistant .
   ```

2. Push to Google Container Registry:
   ```bash
   docker push gcr.io/your-project/pdf-research-assistant
   ```

3. Deploy to Cloud Run:
   ```bash
   gcloud run deploy pdf-research-assistant \
     --image gcr.io/your-project/pdf-research-assistant \
     --platform managed \
     --port 8501 \
     --memory 2Gi
   ```

### Deploying to Azure Container Instances

1. Build and push the Docker image to Azure Container Registry
2. Deploy using Azure CLI:
   ```bash
   az container create \
     --resource-group myResourceGroup \
     --name pdf-research-assistant \
     --image mycontainerregistry.azurecr.io/pdf-research-assistant:latest \
     --dns-name-label pdf-research-assistant \
     --ports 8501 8002
   ```

## Advanced Configuration

### Using External LLM APIs

To use OpenAI or other external LLM APIs instead of Ollama:

1. Set environment variables in `.env` or docker-compose.yml:
   ```
   USE_LOCAL_LLM=false
   OPENAI_API_KEY=your_api_key_here
   ```

2. Restart the application:
   ```bash
   docker-compose down
   docker-compose up -d
   ```

### Persistent Storage

The application uses Docker volumes for persistent storage:

- `./data:/app/data`: Stores uploaded PDFs
- `./models:/app/models`: Stores vector database and embeddings

To backup these directories:

```bash
# Create a backup
tar -czvf pdf-assistant-backup.tar.gz data models

# Restore from backup
tar -xzvf pdf-assistant-backup.tar.gz
```

## Troubleshooting

### Container Fails to Start

Check the logs:
```bash
docker-compose logs pdf-research-assistant
```

### Ollama Connection Issues

Ensure the Ollama container is running:
```bash
docker ps | grep ollama
```

If using local LLM, make sure the model is downloaded:
```bash
docker exec -it ollama ollama list
```

### Memory Issues

If the application crashes due to memory limitations, increase the memory allocation in docker-compose.yml:

```yaml
services:
  pdf-research-assistant:
    deploy:
      resources:
        limits:
          memory: 4G
``` 