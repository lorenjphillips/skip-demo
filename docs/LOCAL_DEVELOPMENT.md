# Local Development Guide

## Quick Start

The fastest way to get started is using the automated script:

```bash
./local-run.sh
```

This handles everything automatically. For manual setup or troubleshooting, continue reading.

## Manual Setup

### 1. Backend Setup

```bash
cd backend

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create environment file
echo "OPENAI_API_KEY=your_api_key_here" > .env
```

### 2. Database Initialization

```bash
# Run data ingestion (creates and populates ChromaDB)
python3 ingest.py
```

Expected output:
```
=== ChromaDB Setup ===
Environment: Development
Database directory: ./chroma_db
...
=== Processing Summary ===
Processed 4 episodes
Total chunks created: 41
Final document count in collection: 41
```

### 3. Start Backend Server

```bash
# Development server with hot reload
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Or without reload
python3 main.py
```

Backend will be available at:
- **API**: http://localhost:8000
- **Docs**: http://localhost:8000/docs
- **Health**: http://localhost:8000/health

### 4. Frontend Setup

```bash
cd ../frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

Frontend will be available at:
- **App**: http://localhost:3000

## Development Workflow

### Project Structure
```
backend/
├── main.py              # FastAPI app with endpoints
├── ingest.py            # Data ingestion script
├── requirements.txt     # Python dependencies
├── .env                 # Environment variables (create this)
├── data/
│   ├── transcripts/     # Episode transcript files
│   └── metadata.json    # Episode metadata
├── chroma_db/          # Local database (auto-created)
└── venv/               # Virtual environment (auto-created)
```

### Adding New Episodes

1. **Add transcript file**:
   ```bash
   # Create new transcript file
   echo "Your transcript content..." > backend/data/transcripts/episode_005.txt
   ```

2. **Update metadata**:
   ```json
   // Add to backend/data/metadata.json
   {
     "episode_005": {
       "title": "New Episode Title",
       "description": "Episode description here",
       "url": "https://podcast-url.com/episode-5"
     }
   }
   ```

3. **Re-ingest data**:
   ```bash
   cd backend
   python3 ingest.py
   ```

### Database Management

**Check database status**:
```bash
# Quick check
curl http://localhost:8000/db-status

# Detailed check
curl http://localhost:8000/debug
```

**Reset database**:
```bash
# Delete local database
rm -rf backend/chroma_db

# Rebuild from scratch
cd backend
python3 ingest.py
```

**Test queries**:
```bash
# Test search functionality
curl -X POST http://localhost:8000/test-query \
  -H "Content-Type: application/json" \
  -d '{"question": "career advice"}'

# Test full AI pipeline
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"question": "What career advice was mentioned?"}'
```

## Development Tools

### Virtual Environment Management

**Activate environment**:
```bash
source backend/venv/bin/activate
```

**Deactivate environment**:
```bash
deactivate
```

**Update dependencies**:
```bash
pip install new-package
pip freeze > requirements.txt
```

### Port Management

**Check what's using ports**:
```bash
lsof -i :8000  # Backend
lsof -i :3000  # Frontend
```

**Kill processes on ports**:
```bash
lsof -ti:8000 | xargs kill -9  # Backend
lsof -ti:3000 | xargs kill -9  # Frontend
```

### Debugging

**Backend logs**:
```bash
# Run with debug logging
uvicorn main:app --reload --log-level debug

# Or add print statements in code for debugging
```

**Database inspection**:
```python
import chromadb

# Connect to local database
client = chromadb.PersistentClient(path="./chroma_db")
collection = client.get_collection("podcast_transcripts")

# Check document count
print(f"Documents: {collection.count()}")

# Peek at data
peek = collection.peek()
print(f"Sample documents: {len(peek['documents'])}")

# Test query
results = collection.query(
    query_texts=["career advice"],
    n_results=2
)
print(f"Search results: {len(results['documents'][0])}")
```

## Troubleshooting

### Common Issues

**Import errors**:
```bash
# Make sure virtual environment is activated
source backend/venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt
```

**Database errors**:
```bash
# Check if database directory exists
ls -la backend/chroma_db/

# Recreate database
rm -rf backend/chroma_db
python3 backend/ingest.py
```

**Port conflicts**:
```bash
# Find and kill conflicting processes
lsof -ti:8000 | xargs kill -9
lsof -ti:3000 | xargs kill -9
```

**OpenAI API errors**:
```bash
# Check if API key is set
cat backend/.env

# Test API key
python3 -c "
import os
from dotenv import load_dotenv
load_dotenv('backend/.env')
print('API Key length:', len(os.getenv('OPENAI_API_KEY', '')))
"
```

**Module not found errors**:
```bash
# Make sure you're in the right directory
pwd  # Should be in skip-demo/backend for backend commands

# Check Python path
python3 -c "import sys; print(sys.path)"
```

### Performance Issues

**Slow startup**:
- First run downloads embedding model (~100MB)
- Subsequent runs should be faster
- Model is cached in `~/.cache/huggingface/`

**Memory usage**:
- ChromaDB loads entire database in memory
- Monitor with `htop` or Activity Monitor
- Consider reducing chunk size if needed

**Query slowness**:
- Check OpenAI API response times
- Monitor embedding generation time
- Verify database size with `/db-status`

## Development Best Practices

### Code Organization
- Keep API endpoints in `main.py`
- Put data processing logic in separate modules
- Use type hints for better code clarity
- Add docstrings to functions

### Testing
```bash
# Test database functionality
python3 -c "
import chromadb
client = chromadb.PersistentClient(path='./chroma_db')
collection = client.get_collection('podcast_transcripts')
print(f'✓ Database working: {collection.count()} docs')
"

# Test API endpoints
curl http://localhost:8000/health
curl http://localhost:8000/db-status
```

### Environment Variables
```bash
# backend/.env example
OPENAI_API_KEY=sk-your-api-key-here
DEBUG=true                    # Optional: enable debug mode
LOG_LEVEL=debug              # Optional: set log level
```

### Git Workflow
```bash
# Never commit sensitive files
echo "backend/.env" >> .gitignore
echo "backend/chroma_db/" >> .gitignore
echo "backend/venv/" >> .gitignore

# Commit changes
git add .
git commit -m "Add new feature"
git push origin main
```

## IDE Configuration

### VS Code Settings
```json
// .vscode/settings.json
{
  "python.defaultInterpreterPath": "./backend/venv/bin/python",
  "python.terminal.activateEnvironment": true,
  "python.analysis.extraPaths": ["./backend"],
  "files.exclude": {
    "**/venv": true,
    "**/chroma_db": true,
    "**/__pycache__": true
  }
}
```

### Recommended Extensions
- Python
- FastAPI
- REST Client (for API testing)
- GitLens
- Docker (if using containers)

This guide covers everything you need for local development. For production deployment, see [PRODUCTION_DEPLOYMENT.md](PRODUCTION_DEPLOYMENT.md).