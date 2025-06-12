# Production Data Ingestion Guide

## Overview
This guide explains how to populate your ChromaDB with podcast transcript data in production environments (Vercel + Render).

## Production Architecture
- **Frontend**: Vercel (static hosting)
- **Backend**: Render (web service with persistent disk)
- **Database**: ChromaDB (persistent volume at `/data/chroma_db`)

## Automatic Data Ingestion

### Current Setup
Your Render deployment is configured with automatic data ingestion via `render.yaml`:

```yaml
preDeployCommand: python ingest.py
```

This means:
1. **Every deployment** runs `python ingest.py` before starting the server
2. Data is automatically populated from `/backend/data/transcripts/` and `/backend/data/metadata.json`
3. The persistent disk at `/data` ensures data survives deployments

### What Happens During Deployment
1. Render builds your Docker container
2. Runs `python ingest.py` (pre-deploy command)
3. Ingestion script:
   - Creates ChromaDB at `/data/chroma_db`
   - Processes all `.txt` files in `data/transcripts/`
   - Uses metadata from `data/metadata.json`
   - Creates searchable chunks with embeddings
4. Starts the main application

## Manual Data Management

### Option 1: Update Source Files and Redeploy
**Best for**: Adding new episodes or updating existing content

1. Add new transcript files to `backend/data/transcripts/`
2. Update `backend/data/metadata.json` with episode metadata
3. Push to your Git repository
4. Render automatically redeploys and re-ingests all data

### Option 2: One-Time Manual Ingestion (Advanced)
**Best for**: Emergency updates or debugging

1. SSH into your Render instance (if available) or use Render Shell
2. Navigate to your app directory
3. Run: `python ingest.py`

### Option 3: API-Based Data Updates (Future Enhancement)
Consider adding endpoints like:
- `POST /admin/ingest` - Trigger manual ingestion
- `POST /admin/episodes` - Add single episode
- `DELETE /admin/episodes/{id}` - Remove episode

## Data Structure Requirements

### Transcript Files
- Location: `backend/data/transcripts/`
- Format: `episode_XXX.txt` (where XXX is the episode ID)
- Content: Plain text transcript

### Metadata File
- Location: `backend/data/metadata.json`
- Format:
```json
{
  "episode_001": {
    "title": "Episode Title",
    "description": "Episode description",
    "url": "https://episode-url.com"
  }
}
```

## Environment Variables

### Required for Production
- `OPENAI_API_KEY`: Your OpenAI API key for embeddings and chat completion
- `RENDER`: Automatically set to "true" by Render platform
- `PORT`: Automatically set by Render (defaults to 8000 in development)

## Troubleshooting Production Data Issues

### Check Database Status
Visit these endpoints to debug data issues:
- `GET /health/ready` - Check if database is initialized
- `GET /db-status` - View database statistics
- `GET /db-check` - Detailed database information
- `GET /debug` - Full database debugging info

### Common Issues

1. **No documents after deployment**
   - Check Render build logs for ingestion errors
   - Verify transcript files exist in `data/transcripts/`
   - Check metadata.json format

2. **Partial data ingestion**
   - Some episodes may lack metadata entries
   - Check ingestion logs for "Warning: No metadata found" messages

3. **Embedding failures**
   - Usually indicates network issues or model download problems
   - Check Render service logs during startup

### Recovery Steps
If data ingestion fails:
1. Check Render deployment logs
2. Verify source data files are correct
3. Manually trigger redeploy in Render dashboard
4. Use debug endpoints to verify data state

## Performance Considerations

### Database Size
- Each episode creates multiple chunks (typically 5-15 per episode)
- Current setup: ~41 chunks for 4 episodes
- Estimated storage: ~1MB per 10 episodes

### Startup Time
- Initial ingestion: 30-60 seconds for full dataset
- Subsequent deployments: Faster if data unchanged
- Model loading: ~10-15 seconds for sentence-transformers

### Scaling
- ChromaDB handles thousands of documents efficiently
- Consider switching to cloud vector DB for 100+ episodes
- Current 1GB disk allocation supports ~500 episodes

## Monitoring
- Monitor deployment success via Render dashboard
- Check application logs for ingestion completion messages
- Use health endpoints for automated monitoring
- Set up alerts for failed deployments