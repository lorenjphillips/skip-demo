# API Reference

## Base URL

- **Local Development**: `http://localhost:8000`
- **Production**: `https://your-app-name.onrender.com`

## Authentication

Currently no authentication required. All endpoints are publicly accessible.

## Content Types

All endpoints accept and return `application/json` unless otherwise specified.

## Health & Status Endpoints

### GET /health

Basic health check endpoint that confirms the service is running.

**Response**:
```json
{
  "status": "healthy"
}
```

**Status Codes**:
- `200 OK`: Service is running

**Example**:
```bash
curl http://localhost:8000/health
```

---

### GET /health/ready

Detailed health check that verifies database initialization and dependencies.

**Response** (Success):
```json
{
  "status": "healthy",
  "chromadb_initialized": true,
  "embedding_model_loaded": true
}
```

**Response** (Error):
```json
{
  "detail": "Service initialization failed: ChromaDB connection error"
}
```

**Status Codes**:
- `200 OK`: All systems ready
- `503 Service Unavailable`: Dependencies not initialized

**Example**:
```bash
curl http://localhost:8000/health/ready
```

## Core Search Endpoints

### POST /query

Main endpoint for semantic search with AI-powered response generation.

**Request Body**:
```json
{
  "question": "string"
}
```

**Response**:
```json
{
  "answer": "AI-generated response based on podcast content",
  "sources": [
    {
      "episode_id": "episode_001",
      "title": "Episode Title",
      "url": "https://episode-url.com"
    }
  ]
}
```

**Status Codes**:
- `200 OK`: Query processed successfully
- `422 Unprocessable Entity`: Invalid request format
- `500 Internal Server Error`: Processing error

**Example**:
```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"question": "What career advice was mentioned in the podcasts?"}'
```

**Response Example**:
```json
{
  "answer": "Based on the podcast transcripts, several key career advice points were mentioned: 1) Focus on building a strong foundation early in your career, 2) Seek mentorship and feedback regularly, 3) Be willing to take calculated risks. This advice was particularly emphasized in Episode 1 about crafting a career framework.",
  "sources": [
    {
      "episode_id": "episode_001",
      "title": "Episode 1: Crafting a career framework",
      "url": ""
    }
  ]
}
```

---

### POST /test-query

Raw search endpoint that returns ChromaDB results without AI processing.

**Request Body**:
```json
{
  "question": "string"
}
```

**Response**:
```json
{
  "status": "success",
  "query": "original question",
  "results": {
    "documents": [["chunk text 1", "chunk text 2"]],
    "metadatas": [
      [
        {
          "episode_id": "episode_001",
          "title": "Episode Title",
          "chunk_index": 0,
          "total_chunks": 10
        }
      ]
    ],
    "distances": [[0.1234, 0.5678]]
  }
}
```

**Status Codes**:
- `200 OK`: Search completed
- `422 Unprocessable Entity`: Invalid request
- `500 Internal Server Error`: Search error

**Example**:
```bash
curl -X POST http://localhost:8000/test-query \
  -H "Content-Type: application/json" \
  -d '{"question": "career advice"}'
```

## Database Information Endpoints

### GET /db-status

Comprehensive database statistics and status information.

**Response**:
```json
{
  "status": "OK",
  "collection_name": "podcast_transcripts",
  "document_count": 41,
  "has_documents": true,
  "sample_documents": ["Sample chunk text..."],
  "sample_metadata": [
    {
      "episode_id": "episode_001",
      "title": "Episode Title"
    }
  ],
  "db_directory": "./chroma_db",
  "directory_contents": ["chroma.sqlite3", "index"]
}
```

**Status Codes**:
- `200 OK`: Always returns 200, check status field for actual state

**Example**:
```bash
curl http://localhost:8000/db-status
```

---

### GET /db-check

Simplified database check with document counts and samples.

**Response**:
```json
{
  "status": "success",
  "total_documents": 41,
  "sample_metadata": [
    {
      "episode_id": "episode_001",
      "title": "Episode 1: Crafting a career framework",
      "chunk_index": 0
    }
  ],
  "sample_text": ["Sample document text..."],
  "total_ids": 41
}
```

**Status Codes**:
- `200 OK`: Check completed

**Example**:
```bash
curl http://localhost:8000/db-check
```

---

### GET /debug

Detailed debugging information including collection details and directory structure.

**Response**:
```json
{
  "collections_count": 1,
  "collection_name": "podcast_transcripts",
  "document_count": 41,
  "has_documents": true,
  "first_few_ids": ["episode_001_chunk_0", "episode_001_chunk_1"],
  "sample_metadata": [...],
  "directory_info": {
    "current_dir": "/app",
    "chroma_dir_exists": true,
    "chroma_contents": ["chroma.sqlite3"]
  }
}
```

**Status Codes**:
- `200 OK`: Debug info retrieved

**Example**:
```bash
curl http://localhost:8000/debug
```

## Test Endpoints

### GET /test

Simple test endpoint to verify API connectivity.

**Response**:
```json
{
  "status": "OK",
  "message": "API is working"
}
```

**Status Codes**:
- `200 OK`: API is responding

**Example**:
```bash
curl http://localhost:8000/test
```

## Interactive Documentation

### GET /docs

Swagger UI documentation interface for interactive API exploration.

**Access**: 
- Local: http://localhost:8000/docs
- Production: https://your-app.onrender.com/docs

### GET /redoc

ReDoc documentation interface (alternative to Swagger).

**Access**:
- Local: http://localhost:8000/redoc  
- Production: https://your-app.onrender.com/redoc

## Error Responses

### Standard Error Format

All endpoints return errors in this format:

```json
{
  "detail": "Error description"
}
```

### Common Error Status Codes

| Code | Meaning | Common Causes |
|------|---------|---------------|
| `400 Bad Request` | Invalid request format | Missing required fields, invalid JSON |
| `422 Unprocessable Entity` | Request validation failed | Invalid data types, missing question field |
| `500 Internal Server Error` | Server processing error | Database connection issues, OpenAI API errors |
| `503 Service Unavailable` | Service dependencies unavailable | Database not initialized, dependencies not loaded |

### Example Error Responses

**422 Validation Error**:
```json
{
  "detail": [
    {
      "loc": ["body", "question"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

**500 Internal Server Error**:
```json
{
  "detail": "OpenAI API request failed: Invalid API key"
}
```

**503 Service Unavailable**:
```json
{
  "detail": "Service initialization failed: ChromaDB connection error"
}
```

## Rate Limiting

Currently no rate limiting implemented. Consider implementing for production:

```python
# Recommended limits
- /query: 10 requests/minute per IP
- /test-query: 20 requests/minute per IP  
- Health endpoints: 60 requests/minute per IP
```

## Request/Response Examples

### Successful Query Flow

1. **Search Request**:
```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What advice was given about product management?"
  }'
```

2. **Response**:
```json
{
  "answer": "The podcast mentioned several key pieces of advice for product management: First, always prioritize user needs over internal preferences. Second, data-driven decision making is crucial but should be balanced with intuition. Third, effective communication with engineering teams is essential for successful product delivery. This advice was shared in Episode 4 about product management strategies.",
  "sources": [
    {
      "episode_id": "episode_004",
      "title": "Episode 4: Product Management Executives share their keys to success in the Tech Industry",
      "url": ""
    }
  ]
}
```

### Raw Search Example

1. **Test Query Request**:
```bash
curl -X POST http://localhost:8000/test-query \
  -H "Content-Type: application/json" \
  -d '{"question": "product management"}'
```

2. **Response**:
```json
{
  "status": "success",
  "query": "product management",
  "results": {
    "documents": [
      [
        "Episode Title: Episode 4: Product Management Executives...",
        "In this episode, we discuss the key strategies that successful product managers use..."
      ]
    ],
    "metadatas": [
      [
        {
          "episode_id": "episode_004",
          "title": "Episode 4: Product Management Executives share their keys to success in the Tech Industry",
          "chunk_index": 0,
          "total_chunks": 14,
          "description": "..."
        }
      ]
    ],
    "distances": [[0.3456, 0.4567]]
  }
}
```

## SDK Examples

### Python

```python
import requests
import json

# Configuration
BASE_URL = "http://localhost:8000"  # or production URL

def search_podcasts(question: str):
    """Search podcasts with AI response"""
    response = requests.post(
        f"{BASE_URL}/query",
        json={"question": question},
        headers={"Content-Type": "application/json"}
    )
    return response.json()

def raw_search(question: str):
    """Raw search without AI processing"""
    response = requests.post(
        f"{BASE_URL}/test-query", 
        json={"question": question}
    )
    return response.json()

def check_health():
    """Check service health"""
    response = requests.get(f"{BASE_URL}/health/ready")
    return response.status_code == 200

# Usage examples
if __name__ == "__main__":
    # Check if service is ready
    if check_health():
        print("✓ Service is ready")
        
        # Perform search
        result = search_podcasts("What career advice was mentioned?")
        print(f"Answer: {result['answer']}")
        print(f"Sources: {len(result['sources'])} episodes")
    else:
        print("✗ Service not ready")
```

### JavaScript/Node.js

```javascript
const axios = require('axios');

const BASE_URL = 'http://localhost:8000'; // or production URL

async function searchPodcasts(question) {
    try {
        const response = await axios.post(`${BASE_URL}/query`, {
            question: question
        });
        return response.data;
    } catch (error) {
        console.error('Search failed:', error.response?.data || error.message);
        throw error;
    }
}

async function checkHealth() {
    try {
        const response = await axios.get(`${BASE_URL}/health/ready`);
        return response.status === 200;
    } catch (error) {
        return false;
    }
}

// Usage example
(async () => {
    if (await checkHealth()) {
        console.log('✓ Service is ready');
        
        const result = await searchPodcasts('What career advice was mentioned?');
        console.log(`Answer: ${result.answer}`);
        console.log(`Sources: ${result.sources.length} episodes`);
    } else {
        console.log('✗ Service not ready');
    }
})();
```

### cURL Examples

```bash
# Basic health check
curl -s http://localhost:8000/health | jq .

# Detailed health check  
curl -s http://localhost:8000/health/ready | jq .

# Search with pretty JSON output
curl -s -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"question": "career advice"}' | jq .

# Database status
curl -s http://localhost:8000/db-status | jq .

# Raw search results
curl -s -X POST http://localhost:8000/test-query \
  -H "Content-Type: application/json" \
  -d '{"question": "product management"}' | jq .
```

This API reference covers all available endpoints and usage patterns. For implementation details, see the source code in `backend/main.py`.