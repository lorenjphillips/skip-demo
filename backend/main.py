# File: backend/main.py

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Optional
import chromadb
from sentence_transformers import SentenceTransformer
import os
from dotenv import load_dotenv
from openai import OpenAI
import json
import traceback

# Load environment variables
load_dotenv()

# Debug environment setup
print("\n=== Startup Diagnostics ===")
print(f"Current working directory: {os.getcwd()}")
print(f"Files in current directory: {os.listdir()}")
print(f"Environment variables available: {list(os.environ.keys())}")

# Initialize FastAPI app
app = FastAPI()

# Check for API key
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError(
        "No OpenAI API key found. Please ensure you have a .env file with OPENAI_API_KEY set or "
        "that the environment variable is set."
    )

print("\n=== API Key Check ===")
print("OpenAI API key loaded successfully")
print(f"API key length: {len(api_key)}")

# Add CORS middleware
CORS_ORIGINS = [
    "http://localhost:3000",
    "https://skip-demo-47sqo5zkn-lorenphillips-protonmailcs-projects.vercel.app",
    "https://theskipai.com"
]
print("\n=== CORS Setup ===")
print(f"Configured CORS origins: {CORS_ORIGINS}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Initialize OpenAI client
client = OpenAI(api_key=api_key)
print("\n=== OpenAI Client Initialized ===")

# Initialize ChromaDB
COLLECTION_NAME = "podcast_transcripts"
DB_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "chroma_db")
print(f"\n=== ChromaDB Setup ===")
print(f"Database directory: {DB_DIR}")

# Create the directory if it doesn't exist
os.makedirs(DB_DIR, exist_ok=True)
print(f"Database directory exists: {os.path.exists(DB_DIR)}")

# Initialize the client
chroma_client = chromadb.PersistentClient(path=DB_DIR)
print("ChromaDB client initialized")

def get_or_create_collection():
    try:
        collections = chroma_client.list_collections()
        print(f"Existing collections: {[c.name for c in collections]}")
        
        for collection in collections:
            if collection.name == COLLECTION_NAME:
                print(f"Found existing collection: {COLLECTION_NAME}")
                # Get collection size
                results = collection.get()
                print(f"Collection size: {len(results['ids']) if results else 0} documents")
                return collection
        
        print(f"Creating new collection: {COLLECTION_NAME}")
        return chroma_client.create_collection(name=COLLECTION_NAME)
    except Exception as e:
        print(f"Error in get_or_create_collection: {str(e)}")
        raise e

# Initialize the collection
collection = get_or_create_collection()
print(f"Collection ready: {collection.name}")

# Initialize the embedding model
embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
print("\n=== Embedding Model Initialized ===")

class Query(BaseModel):
    question: str

@app.get("/test")
async def test_endpoint():
    try:
        print("\n=== Test Endpoint Called ===")
        response = {
            "status": "checking",
            "checks": {}
        }
        
        # Test ChromaDB
        try:
            print("Testing ChromaDB...")
            results = collection.get()
            doc_count = len(results['ids']) if results else 0
            print(f"Found {doc_count} documents in collection")
            
            query_results = collection.query(
                query_texts=["test"],
                n_results=1
            )
            response["checks"]["chromadb"] = {
                "status": "ok",
                "total_documents": doc_count,
                "query_results_found": len(query_results['documents'][0]) if query_results['documents'] else 0
            }
        except Exception as e:
            print(f"ChromaDB test error: {str(e)}")
            response["checks"]["chromadb"] = {
                "status": "error",
                "error": str(e)
            }
        
        # Test OpenAI
        try:
            print("Testing OpenAI connection...")
            test_completion = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": "Hello"}]
            )
            response["checks"]["openai"] = {
                "status": "ok",
                "model": "gpt-3.5-turbo"
            }
        except Exception as e:
            print(f"OpenAI test error: {str(e)}")
            response["checks"]["openai"] = {
                "status": "error",
                "error": str(e)
            }
        
        response["status"] = "ok"
        return response
    except Exception as e:
        print(f"Test endpoint error: {str(e)}")
        return {"error": str(e)}

@app.get("/debug-stats")
async def debug_stats():
    try:
        print("\n=== Debug Stats Called ===")
        # Get collection info
        results = collection.get()
        print(f"Retrieved {len(results['ids']) if results else 0} documents")
        
        unique_episodes = set()
        for metadata in results['metadatas']:
            if metadata and 'episode_id' in metadata:
                unique_episodes.add(metadata['episode_id'])
        
        print(f"Found {len(unique_episodes)} unique episodes")

        collection_stats = {
            "name": collection.name,
            "total_chunks": len(results['ids']) if results else 0,
            "unique_episodes": len(unique_episodes),
            "episode_ids": list(unique_episodes)
        }
        
        # Sample query
        print("Performing sample query...")
        sample_results = collection.query(
            query_texts=["test query"],
            n_results=1,
            include_distances=True
        )
        
        return {
            "collection_stats": collection_stats,
            "sample_query_results": {
                "number_of_matches": len(sample_results['documents'][0]) if sample_results['documents'] else 0,
                "similarity_scores": sample_results['distances'][0] if sample_results['distances'] else None,
                "sample_metadata": sample_results['metadatas'][0] if sample_results['metadatas'] else None
            }
        }
    except Exception as e:
        print(f"Debug stats error: {str(e)}")
        return {"error": str(e)}

@app.post("/query")
async def query_transcripts(query: Query):
    try:
        print("\n=== Query Endpoint Called ===")
        print(f"Question received: {query.question}")
        
        # Query the collection
        print("\nExecuting query...")
        results = collection.query(
            query_texts=[query.question],
            n_results=2
        )
        
        print(f"\nQuery results:")
        print(f"Documents found: {len(results['documents']) if results['documents'] else 0}")
        print(f"Has documents: {bool(results['documents'] and results['documents'][0])}")
        
        if results['documents'] and results['documents'][0]:
            print("\nFirst matching document:")
            print(results['documents'][0][0][:200])
            print("\nMetadata:")
            print(results['metadatas'][0])
            
            # Create context and generate response
            context = "\n".join(results['documents'][0])
            
            print("\nGenerating OpenAI response...")
            completion = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "system", 
                        "content": "You are a helpful assistant that answers questions about the Skip Podcast. " +
                                "Always cite the specific episode title in your response, and provide detailed " +
                                "answers based on the context provided."
                    },
                    {
                        "role": "user", 
                        "content": f"Context from podcast transcripts:\n{context}\n\nQuestion: {query.question}"
                    }
                ],
                temperature=0.7,
                max_tokens=500
            )
            
            answer = completion.choices[0].message.content
            print(f"\nGenerated answer: {answer[:200]}...")
            
            # Prepare sources
            sources = [
                {
                    "episode_id": meta['episode_id'],
                    "title": meta['title'],
                    "url": meta.get('url', '')
                }
                for meta in results['metadatas'][0]
            ]
            
            return JSONResponse(content={
                "answer": answer,
                "sources": sources
            })
        else:
            print("\nNo matching documents found")
            return JSONResponse(content={
                "answer": "I couldn't find any relevant information in the podcast transcripts.",
                "sources": []
            })
            
    except Exception as e:
        print(f"\nError in query_transcripts:")
        print(f"Type: {type(e).__name__}")
        print(f"Error: {str(e)}")
        print(f"Traceback: {traceback.format_exc()}")
        return JSONResponse(
            status_code=500,
            content={"detail": str(e)}
        )

@app.get("/health")
async def health_check():
    try:
        print("\n=== Health Check Called ===")
        # Test database connection
        collection_status = "OK" if collection else "Not Connected"
        # Test OpenAI connection
        openai_status = "OK" if api_key else "Not Connected"
        
        return {
            "status": "healthy",
            "version": "1.0.0",
            "database": collection_status,
            "openai": openai_status,
            "cors_origins": CORS_ORIGINS
        }
    except Exception as e:
        print(f"Health check error: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={
                "status": "unhealthy",
                "error": str(e)
            }
        )
    
# Add these imports at the top if not already present
from datetime import datetime
import sys

# Add these endpoints to your main.py
@app.get("/logs")
async def get_logs():
    try:
        print("\n=== Logs Endpoint Called ===")
        # Get collection state
        results = collection.get()
        doc_count = len(results['ids']) if results else 0
        
        debug_info = {
            "timestamp": datetime.now().isoformat(),
            "application_status": {
                "openai_key_configured": bool(api_key),
                "cors_origins": CORS_ORIGINS,
            },
            "database_stats": {
                "total_documents": doc_count,
                "collection_name": collection.name,
                "db_directory": DB_DIR,
                "db_exists": os.path.exists(DB_DIR)
            },
            "collection_info": {
                "documents_count": doc_count,
                "unique_episodes": len(set(meta['episode_id'] for meta in results['metadatas'])) if results and results['metadatas'] else 0
            }
        }
        
        # Add sample document if available
        if doc_count > 0:
            sample_doc = {
                "first_document_id": results['ids'][0],
                "first_document_metadata": results['metadatas'][0],
                "content_preview": results['documents'][0][:200] + "..." if results['documents'] else "No content"
            }
            debug_info["sample_document"] = sample_doc
        
        return JSONResponse(content=debug_info)
    except Exception as e:
        print(f"Error in logs endpoint: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={
                "error": str(e),
                "traceback": traceback.format_exc()
            }
        )

@app.get("/logs/query-test")
async def test_query():
    try:
        print("\n=== Query Test Endpoint Called ===")
        test_questions = [
            "What is the career framework?",
            "Tell me about the podcast",
            "What topics are covered?"
        ]
        
        results = []
        for question in test_questions:
            print(f"\nTesting question: {question}")
            query_results = collection.query(
                query_texts=[question],
                n_results=1
            )
            
            results.append({
                "question": question,
                "matches_found": len(query_results['documents'][0]) if query_results['documents'] else 0,
                "sample_match": query_results['documents'][0][0][:100] + "..." if query_results['documents'] and query_results['documents'][0] else "No match"
            })
        
        return JSONResponse(content={
            "timestamp": datetime.now().isoformat(),
            "test_results": results
        })
    except Exception as e:
        print(f"Error in query test endpoint: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={
                "error": str(e),
                "traceback": traceback.format_exc()
            }
        )

if __name__ == "__main__":
    import uvicorn
    print("\n=== Starting Server ===")
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="debug")