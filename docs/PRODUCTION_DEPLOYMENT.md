# Production Deployment Guide

## Overview

This application uses a two-service architecture:
- **Frontend**: Vercel (static hosting)
- **Backend**: Render (web service with persistent storage)

## Prerequisites

- GitHub repository with your code
- Vercel account
- Render account  
- OpenAI API key

## Backend Deployment (Render)

### 1. Initial Setup

1. **Connect GitHub Repository**:
   - Go to [Render Dashboard](https://dashboard.render.com/)
   - Click "New" → "Web Service"
   - Connect your GitHub repository
   - Select the repository containing your code

2. **Configure Service**:
   - **Name**: `skip-demo-backend` (or your preferred name)
   - **Root Directory**: Leave blank (uses repo root)
   - **Runtime**: Docker
   - **Build Command**: Automatically detected from `render.yaml`
   - **Start Command**: Automatically detected from `render.yaml`

### 2. Environment Variables

Set these in the Render dashboard under "Environment":

| Variable | Value | Description |
|----------|-------|-------------|
| `OPENAI_API_KEY` | `sk-your-key-here` | Your OpenAI API key |

**Note**: `RENDER` and `PORT` are automatically set by the platform.

### 3. Service Configuration

The `render.yaml` file in your repository root configures:

```yaml
services:
  - type: web
    name: skip-demo-backend
    runtime: docker
    plan: starter
    region: oregon
    dockerfilePath: ./backend/Dockerfile
    dockerContext: ./backend
    buildCommand: pip install -r requirements.txt
    startCommand: uvicorn main:app --host 0.0.0.0 --port $PORT
    healthCheckPath: /health
    preDeployCommand: python ingest.py
    envVars:
      - key: OPENAI_API_KEY
        sync: false
      - key: RAILWAY_ENVIRONMENT
        value: production
      - key: PORT
        value: 8000
    disk:
      name: chroma-data
      mountPath: /data
      sizeGB: 1
```

### 4. Deploy

1. Click "Create Web Service"
2. Render will:
   - Build the Docker container
   - Run `python ingest.py` (pre-deploy command)
   - Start the application
   - Mount persistent disk at `/data`

### 5. Verify Deployment

Once deployed, test these endpoints:

```bash
# Replace YOUR_RENDER_URL with your actual Render URL
export BACKEND_URL="https://your-app-name.onrender.com"

# Basic health check
curl $BACKEND_URL/health

# Database status
curl $BACKEND_URL/db-status

# Test query
curl -X POST $BACKEND_URL/query \
  -H "Content-Type: application/json" \
  -d '{"question": "What career advice was mentioned?"}'
```

## Frontend Deployment (Vercel)

### 1. Initial Setup

1. **Connect GitHub Repository**:
   - Go to [Vercel Dashboard](https://vercel.com/dashboard)
   - Click "New Project"
   - Import your GitHub repository

2. **Configure Project**:
   - **Framework Preset**: Next.js
   - **Root Directory**: `frontend`
   - **Build Command**: `npm run build`
   - **Output Directory**: `.next`

### 2. Environment Variables

Set these in Vercel dashboard under "Settings" → "Environment Variables":

| Variable | Value | Description |
|----------|-------|-------------|
| `NEXT_PUBLIC_API_URL` | `https://your-render-app.onrender.com` | Backend API URL |

### 3. Deploy

1. Click "Deploy"
2. Vercel will:
   - Install dependencies
   - Build the Next.js application
   - Deploy to global CDN

### 4. Update CORS Settings

After frontend deployment, update your backend CORS settings in `backend/main.py`:

```python
CORS_ORIGINS = [
    "http://localhost:3000",  # Local development
    "https://your-vercel-app.vercel.app",  # Add your Vercel URL
    "https://your-custom-domain.com",  # Add custom domain if applicable
]
```

Redeploy the backend after updating CORS settings.

## Data Management in Production

### Automatic Data Ingestion

**Every backend deployment** automatically runs data ingestion:

1. `preDeployCommand: python ingest.py` in `render.yaml`
2. Processes all files in `backend/data/transcripts/`
3. Uses metadata from `backend/data/metadata.json`
4. Populates ChromaDB at `/data/chroma_db`

### Adding New Episodes

1. **Add transcript file**:
   ```
   backend/data/transcripts/episode_XXX.txt
   ```

2. **Update metadata**:
   ```json
   // backend/data/metadata.json
   {
     "episode_XXX": {
       "title": "Episode Title",
       "description": "Episode description",
       "url": "https://episode-url.com"
     }
   }
   ```

3. **Deploy**:
   ```bash
   git add .
   git commit -m "Add episode XXX"
   git push origin main
   ```

4. **Render auto-redeploys** and re-ingests all data

### Manual Data Operations

**Trigger manual ingestion** (if needed):
```bash
# Use Render Shell or SSH (if available)
cd /opt/render/project/src
python ingest.py
```

**Check data status**:
```bash
curl https://your-app.onrender.com/db-status
curl https://your-app.onrender.com/debug
```

## Monitoring and Maintenance

### Health Checks

Render automatically monitors:
- **Health endpoint**: `/health`
- **Response time**: Should be < 30s
- **Status codes**: Expects 200 responses

### Logging

**View logs**:
1. Go to Render dashboard
2. Select your service
3. Click "Logs" tab

**Common log patterns**:
```
# Successful startup
=== ChromaDB Setup ===
Collection 'podcast_transcripts' contains X documents

# Successful query
Query results: 2 documents found

# Errors to watch for
Error during processing: ...
ChromaDB health check failed: ...
```

### Performance Monitoring

**Key metrics to monitor**:
- Response time (< 5s for queries)
- Memory usage (< 80% of available)
- Disk usage (< 80% of 1GB)
- Error rate (< 1%)

**Render provides**:
- CPU and memory charts
- Request/response metrics
- Uptime monitoring

### Scaling Considerations

**Current limits**:
- **Plan**: Starter (512MB RAM, 0.1 CPU)
- **Storage**: 1GB persistent disk
- **Concurrent requests**: ~10-20

**Upgrade options**:
- **Standard plan**: 2GB RAM, 1 CPU
- **Pro plan**: 4GB RAM, 2 CPU
- **Disk expansion**: Up to 100GB

## Environment Configuration

### Production Environment Detection

The app detects production environment via:
```python
IS_PRODUCTION = os.getenv("RENDER") == "true"
```

**Production differences**:
- Database path: `/data/chroma_db` (persistent disk)
- Error handling: More conservative
- Logging: Structured JSON logs
- CORS: Restricted origins

### Required Environment Variables

| Variable | Source | Purpose |
|----------|---------|---------|
| `RENDER` | Auto-set by platform | Environment detection |
| `PORT` | Auto-set by platform | Server port |
| `OPENAI_API_KEY` | Manual configuration | AI functionality |

## Security Configuration

### API Security

**CORS settings**:
```python
CORS_ORIGINS = [
    "https://your-frontend-domain.com",
    "https://your-vercel-app.vercel.app"
]
```

**Rate limiting** (recommended addition):
```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.post("/query")
@limiter.limit("10/minute")
async def query(request: Request, query: Query):
    # ... existing code
```

### Data Security

**Sensitive data handling**:
- API keys stored as environment variables
- No user data persistence beyond queries
- Transcript data is public podcast content

**Backup recommendations**:
- Regular database backups via Render disk snapshots
- Source data versioning in Git
- API key rotation procedures

## Troubleshooting Production Issues

### Common Deployment Issues

**Build failures**:
```bash
# Check Render build logs
# Common causes:
# - Missing dependencies in requirements.txt
# - Python version compatibility
# - Dockerfile syntax errors
```

**Health check failures**:
```bash
# Check if these endpoints respond:
curl https://your-app.onrender.com/health
curl https://your-app.onrender.com/health/ready

# Common causes:
# - Database initialization timeout
# - OpenAI API key issues
# - Memory limits exceeded
```

**Data ingestion failures**:
```bash
# Check logs for:
# - "Processing completed successfully"
# - "Error during processing"
# - File not found errors

# Verify source data exists:
ls backend/data/transcripts/
cat backend/data/metadata.json
```

### Performance Issues

**Slow responses**:
- Check OpenAI API status
- Monitor Render resource usage
- Consider upgrading plan

**Memory issues**:
- ChromaDB loads entirely in memory
- Monitor with Render metrics
- Consider data archiving for large datasets

**Disk space issues**:
- Current limit: 1GB
- Monitor via `/db-status` endpoint
- Upgrade disk if needed

### Recovery Procedures

**Complete data reset**:
1. Delete disk snapshots (if any)
2. Redeploy service (triggers fresh ingestion)
3. Verify via `/db-status` endpoint

**Rollback deployment**:
1. Go to Render dashboard
2. Select previous deployment
3. Click "Redeploy"

**Emergency maintenance**:
1. Set Render service to "Suspended"
2. Fix issues in code
3. Redeploy and resume

## Cost Optimization

### Current Costs (Render Starter)
- **Web service**: $7/month
- **Persistent disk**: $0.25/GB/month ($0.25/month for 1GB)
- **Total**: ~$7.25/month

### Optimization Strategies
- Monitor resource usage via Render dashboard
- Implement caching for frequent queries
- Optimize embedding model size if needed
- Consider scheduled deployments vs continuous

This guide covers all aspects of production deployment. For development setup, see [LOCAL_DEVELOPMENT.md](LOCAL_DEVELOPMENT.md).