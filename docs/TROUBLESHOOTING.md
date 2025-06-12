# Troubleshooting Guide

## Quick Diagnostics

Run these commands to quickly identify issues:

```bash
# Check service health
curl http://localhost:8000/health

# Check database status  
curl http://localhost:8000/db-status

# Test basic functionality
curl -X POST http://localhost:8000/test-query \
  -H "Content-Type: application/json" \
  -d '{"question": "test"}'
```

## Common Issues

### 1. Local Development Issues

#### Service Won't Start

**Symptom**: `./local-run.sh` fails or backend doesn't start

**Diagnosis**:
```bash
# Check if ports are in use
lsof -i :8000
lsof -i :3000

# Check Python environment
which python3
python3 --version

# Check if in correct directory
pwd  # Should be in skip-demo directory
ls   # Should see backend/ and frontend/ folders
```

**Solutions**:
```bash
# Kill conflicting processes
lsof -ti:8000 | xargs kill -9
lsof -ti:3000 | xargs kill -9

# Reset and restart
rm -rf backend/venv backend/chroma_db
./local-run.sh
```

---

#### Virtual Environment Issues

**Symptom**: "Module not found" or import errors

**Diagnosis**:
```bash
# Check if virtual environment is activated
echo $VIRTUAL_ENV  # Should show path to venv

# Check installed packages
pip list | grep -E "(fastapi|chromadb|openai)"
```

**Solutions**:
```bash
# Recreate virtual environment
cd backend
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

---

#### Database Issues

**Symptom**: "Collection not found" or "No documents in database"

**Diagnosis**:
```bash
# Check if database directory exists
ls -la backend/chroma_db/

# Check ingestion logs
cd backend
python3 ingest.py 2>&1 | grep -E "(Error|Processing|completed)"

# Test database directly
python3 -c "
import chromadb
client = chromadb.PersistentClient(path='./chroma_db')
try:
    collection = client.get_collection('podcast_transcripts')
    print(f'✓ Collection found with {collection.count()} documents')
except Exception as e:
    print(f'✗ Database error: {e}')
"
```

**Solutions**:
```bash
# Reset database
rm -rf backend/chroma_db
cd backend
python3 ingest.py

# Check source data
ls backend/data/transcripts/
cat backend/data/metadata.json | jq .
```

---

#### OpenAI API Issues

**Symptom**: "Invalid API key" or OpenAI-related errors

**Diagnosis**:
```bash
# Check if API key is set
cat backend/.env | grep OPENAI_API_KEY

# Test API key length (should be ~51+ characters)
python3 -c "
import os
from dotenv import load_dotenv
load_dotenv('backend/.env')
key = os.getenv('OPENAI_API_KEY', '')
print(f'Key length: {len(key)}')
print(f'Key prefix: {key[:7]}...')
"

# Test API connection
python3 -c "
from openai import OpenAI
import os
from dotenv import load_dotenv
load_dotenv('.env')
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
try:
    models = client.models.list()
    print('✓ OpenAI API connection successful')
except Exception as e:
    print(f'✗ OpenAI API error: {e}')
"
```

**Solutions**:
```bash
# Create or update .env file
echo "OPENAI_API_KEY=sk-your-real-api-key-here" > backend/.env

# Verify API key at https://platform.openai.com/api-keys
# Check billing and usage limits
```

### 2. Production Issues

#### Render Deployment Failures

**Symptom**: Build or deployment fails on Render

**Diagnosis**:
```bash
# Check build logs in Render dashboard
# Look for these common errors:

# 1. Dependencies issues
Error: Could not install packages due to an EnvironmentError

# 2. Disk space issues  
No space left on device

# 3. Timeout issues
Build timed out after 900 seconds

# 4. Environment variable issues
KeyError: 'OPENAI_API_KEY'
```

**Solutions**:

1. **Dependencies issues**:
   - Verify `requirements.txt` is correct
   - Check Python version compatibility
   - Clear Render build cache

2. **Disk space issues**:
   - Upgrade Render plan
   - Optimize Docker image size
   - Clean up build artifacts

3. **Timeout issues**:
   - Optimize build process
   - Reduce dependencies if possible
   - Contact Render support

4. **Environment variables**:
   - Check Render dashboard → Environment
   - Verify `OPENAI_API_KEY` is set
   - Check variable naming (case-sensitive)

---

#### Health Check Failures

**Symptom**: Render shows service as unhealthy

**Diagnosis**:
```bash
# Test health endpoints
curl https://your-app.onrender.com/health
curl https://your-app.onrender.com/health/ready

# Check Render logs for errors
# Common patterns:
ChromaDB initialization failed
OpenAI API key not found
Collection not found
```

**Solutions**:

1. **Database initialization issues**:
   ```bash
   # Check pre-deploy command logs
   # Verify data files are included in build
   # Check disk mounting at /data
   ```

2. **API key issues**:
   ```bash
   # Verify OPENAI_API_KEY in Render environment
   # Check key is active and has credits
   # Test key locally first
   ```

3. **Memory issues**:
   ```bash
   # Monitor Render resource usage
   # Consider upgrading plan
   # Optimize memory usage
   ```

---

#### Performance Issues

**Symptom**: Slow responses or timeouts

**Diagnosis**:
```bash
# Test response times
time curl -X POST https://your-app.onrender.com/query \
  -H "Content-Type: application/json" \
  -d '{"question": "test"}'

# Check Render metrics
# Monitor CPU and memory usage
# Check OpenAI API response times
```

**Solutions**:

1. **Upgrade Render plan** for more resources
2. **Optimize queries**:
   ```python
   # Reduce n_results in ChromaDB queries
   results = collection.query(
       query_texts=[question],
       n_results=1  # Reduce from 2 to 1
   )
   ```
3. **Implement caching** for frequent queries
4. **Optimize embedding model** or use smaller model

### 3. Data Issues

#### Missing Episodes

**Symptom**: Some episodes don't appear in search results

**Diagnosis**:
```bash
# Check data files
ls backend/data/transcripts/
cat backend/data/metadata.json | jq 'keys[]'

# Check ingestion logs
python3 backend/ingest.py 2>&1 | grep -E "(Warning|Error|Processing)"

# Test specific episode
curl -X POST http://localhost:8000/test-query \
  -H "Content-Type: application/json" \
  -d '{"question": "episode_005"}' # Replace with missing episode
```

**Solutions**:

1. **Missing metadata**:
   ```json
   // Add missing episode to metadata.json
   {
     "episode_005": {
       "title": "Missing Episode Title",
       "description": "Episode description",
       "url": ""
     }
   }
   ```

2. **File naming issues**:
   ```bash
   # Ensure files match pattern: episode_XXX.txt
   ls backend/data/transcripts/ | grep -v "episode_[0-9]"
   ```

3. **Re-run ingestion**:
   ```bash
   cd backend
   python3 ingest.py
   ```

---

#### Poor Search Results

**Symptom**: Search doesn't find relevant content

**Diagnosis**:
```bash
# Test different query styles
curl -X POST http://localhost:8000/test-query \
  -H "Content-Type: application/json" \
  -d '{"question": "exact phrase from transcript"}'

# Check chunk content
curl http://localhost:8000/db-status | jq '.sample_documents[0]'
```

**Solutions**:

1. **Adjust chunking parameters** in `ingest.py`:
   ```python
   # Smaller chunks for better precision
   chunks = self.chunk_transcript(full_content, chunk_size=500, overlap=50)
   ```

2. **Improve query phrasing**:
   ```bash
   # Instead of: "career"
   # Try: "career advice" or "career development"
   ```

3. **Add more context** to search:
   ```python
   # Modify the system prompt in main.py
   "You are a helpful assistant that answers questions about the Skip Podcast..."
   ```

### 4. Development Environment Issues

#### Docker Issues (if using Docker)

**Symptom**: Docker build or run failures

**Diagnosis**:
```bash
# Check Docker daemon
docker --version
docker info

# Check Dockerfile syntax
cd backend
docker build -t skip-demo-test .

# Check container logs
docker run -p 8000:8000 skip-demo-test
```

**Solutions**:
```bash
# Clean Docker environment
docker system prune -f
docker build --no-cache -t skip-demo-test .

# Check port mapping
docker run -p 8000:8000 -e OPENAI_API_KEY=sk-... skip-demo-test
```

---

#### Frontend Issues

**Symptom**: Frontend won't start or connect to backend

**Diagnosis**:
```bash
# Check Node.js version
node --version  # Should be 18+
npm --version

# Check dependencies
cd frontend
npm list

# Check backend connectivity
curl http://localhost:8000/health
```

**Solutions**:
```bash
# Reset frontend
cd frontend
rm -rf node_modules package-lock.json
npm install

# Update API URL if needed
# Check environment variables in frontend/.env.local
```

### 5. Performance Debugging

#### Memory Issues

**Diagnosis**:
```bash
# Monitor memory usage
# On macOS/Linux:
top -p $(pgrep -f "python.*main.py")

# Check ChromaDB memory usage
python3 -c "
import chromadb
import psutil
import os

# Memory before
mem_before = psutil.Process(os.getpid()).memory_info().rss / 1024 / 1024

client = chromadb.PersistentClient(path='./chroma_db')
collection = client.get_collection('podcast_transcripts')

# Memory after
mem_after = psutil.Process(os.getpid()).memory_info().rss / 1024 / 1024

print(f'Memory usage: {mem_before:.1f}MB → {mem_after:.1f}MB')
print(f'ChromaDB loaded: {collection.count()} documents')
"
```

**Solutions**:
1. **Optimize chunk size** to reduce memory usage
2. **Implement pagination** for large datasets
3. **Use smaller embedding model**
4. **Add memory monitoring** and alerts

---

#### Slow Queries

**Diagnosis**:
```bash
# Profile query performance
time curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"question": "career advice"}'

# Check individual components
python3 -c "
import time
from sentence_transformers import SentenceTransformer

# Time embedding generation
start = time.time()
model = SentenceTransformer('all-MiniLM-L6-v2')
embeddings = model.encode(['test query'])
print(f'Embedding time: {time.time() - start:.2f}s')
"
```

**Solutions**:
1. **Cache embeddings** for common queries
2. **Optimize n_results** parameter
3. **Use faster embedding model**
4. **Implement query preprocessing**

## Diagnostic Scripts

### Health Check Script

Save as `backend/health_check.py`:

```python
#!/usr/bin/env python3
import requests
import sys
import json

def check_health():
    base_url = "http://localhost:8000"
    
    tests = [
        ("Basic health", f"{base_url}/health"),
        ("Ready check", f"{base_url}/health/ready"),
        ("Database status", f"{base_url}/db-status"),
    ]
    
    results = []
    for name, url in tests:
        try:
            response = requests.get(url, timeout=10)
            status = "✓" if response.status_code == 200 else "✗"
            results.append(f"{status} {name}: {response.status_code}")
        except Exception as e:
            results.append(f"✗ {name}: {str(e)}")
    
    # Test query
    try:
        response = requests.post(
            f"{base_url}/test-query",
            json={"question": "test"},
            timeout=30
        )
        status = "✓" if response.status_code == 200 else "✗"
        results.append(f"{status} Query test: {response.status_code}")
    except Exception as e:
        results.append(f"✗ Query test: {str(e)}")
    
    print("\n".join(results))
    return all("✓" in result for result in results)

if __name__ == "__main__":
    success = check_health()
    sys.exit(0 if success else 1)
```

Usage:
```bash
cd backend
python3 health_check.py
```

### Database Diagnostic Script

Save as `backend/db_diagnostic.py`:

```python
#!/usr/bin/env python3
import chromadb
import os
import json

def diagnose_database():
    print("=== Database Diagnostic ===")
    
    # Check if database exists
    db_path = "./chroma_db"
    print(f"Database path: {db_path}")
    print(f"Database exists: {os.path.exists(db_path)}")
    
    if os.path.exists(db_path):
        print(f"Database contents: {os.listdir(db_path)}")
    
    # Try to connect
    try:
        client = chromadb.PersistentClient(path=db_path)
        collections = client.list_collections()
        print(f"Collections: {len(collections)}")
        
        if collections:
            collection = collections[0]
            print(f"Collection name: {collection.name}")
            print(f"Document count: {collection.count()}")
            
            if collection.count() > 0:
                peek = collection.peek()
                print(f"Sample IDs: {peek['ids'][:3]}")
                print(f"Sample metadata: {peek['metadatas'][:1]}")
        
    except Exception as e:
        print(f"Database error: {e}")
    
    # Check source data
    print("\n=== Source Data ===")
    transcripts_dir = "./data/transcripts"
    metadata_file = "./data/metadata.json"
    
    print(f"Transcripts directory exists: {os.path.exists(transcripts_dir)}")
    if os.path.exists(transcripts_dir):
        files = [f for f in os.listdir(transcripts_dir) if f.endswith('.txt')]
        print(f"Transcript files: {len(files)}")
        print(f"Files: {files}")
    
    print(f"Metadata file exists: {os.path.exists(metadata_file)}")
    if os.path.exists(metadata_file):
        try:
            with open(metadata_file, 'r') as f:
                metadata = json.load(f)
            print(f"Metadata entries: {len(metadata)}")
            print(f"Episode IDs: {list(metadata.keys())}")
        except Exception as e:
            print(f"Metadata error: {e}")

if __name__ == "__main__":
    diagnose_database()
```

Usage:
```bash
cd backend
python3 db_diagnostic.py
```

## Getting Help

### Log Collection

When reporting issues, collect these logs:

```bash
# Local development logs
./local-run.sh > setup.log 2>&1

# Backend logs
cd backend
python3 main.py > backend.log 2>&1 &

# Database diagnostic
python3 db_diagnostic.py > db_diag.log

# Health check
python3 health_check.py > health.log
```

### Render Production Logs

1. Go to Render dashboard
2. Select your service
3. Click "Logs" tab
4. Copy relevant error messages
5. Include build logs if deployment failed

### Issue Template

When reporting issues, include:

1. **Environment**: Local development or production (Render)
2. **Symptoms**: What's not working
3. **Error messages**: Exact error text
4. **Steps to reproduce**: What you did before the issue
5. **Logs**: Relevant log excerpts
6. **System info**: OS, Python version, Node version

### Contact Points

- **GitHub Issues**: For bugs and feature requests
- **Documentation**: Check `/docs` folder for guides
- **API Reference**: `/docs` endpoint for interactive testing

This troubleshooting guide covers the most common issues. For additional help, consult the other documentation files or open a GitHub issue.