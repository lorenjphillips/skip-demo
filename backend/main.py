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
from contextlib import asynccontextmanager

# Load environment variables
load_dotenv()

# Debug environment setup
print("\n=== Startup Diagnostics ===")
print(f"Current working directory: {os.getcwd()}")
print(f"Files in current directory: {os.listdir()}")
print(f"Environment variables available: {list(os.environ.keys())}")

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

# Initialize OpenAI client
client = OpenAI(api_key=api_key)
print("\n=== OpenAI Client Initialized ===")

# Constants
COLLECTION_NAME = "podcast_transcripts"
IS_PRODUCTION = os.getenv("RENDER") == "true"
DB_DIR = "/data/chroma_db" if IS_PRODUCTION else "./chroma_db"

# Global variables to track initialization status
chroma_client = None
collection = None
embedding_model = None
initialization_error = None

async def initialize_dependencies():
    global chroma_client, collection, embedding_model, initialization_error
    
    try:
        print(f"\n=== ChromaDB Setup ===")
        print(f"Environment: {'Production' if IS_PRODUCTION else 'Development'}")
        print(f"Database directory: {DB_DIR}")
        
        # Ensure directory exists
        os.makedirs(DB_DIR, exist_ok=True)
        print(f"Database directory exists: {os.path.exists(DB_DIR)}")
        
        # Initialize ChromaDB client
        chroma_client = chromadb.PersistentClient(
            path=DB_DIR,
            settings=chromadb.Settings(
                anonymized_telemetry=False,
                allow_reset=False,
                is_persistent=True
            )
        )
        
        # Initialize collection
        collection = chroma_client.get_or_create_collection(name=COLLECTION_NAME)
        print(f"Collection '{COLLECTION_NAME}' initialized with {collection.count()} documents")
        
        # Initialize embedding model
        embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        print("\n=== Embedding Model Initialized ===")
        
        return True
    except Exception as e:
        initialization_error = str(e)
        print(f"Initialization error: {initialization_error}")
        return False

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await initialize_dependencies()
    yield
    # Shutdown logic would go here if needed

app = FastAPI(lifespan=lifespan)

# CORS configuration
CORS_ORIGINS = [
    "http://localhost:3000",
    "https://skip-demo-47sqo5zkn-lorenphillips-protonmailcs-projects.vercel.app",
    "https://theskipai.com",
    "https://www.theskipai.com",  # Added www subdomain
    "https://*.vercel.app",
    "*"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"]
)

@app.get("/health")
async def health_check():
    """Basic health check that just confirms the service is running"""
    return {"status": "healthy"}

@app.get("/health/ready")
async def readiness_check():
    """Detailed health check including ChromaDB initialization status"""
    if initialization_error:
        raise HTTPException(
            status_code=503,
            detail=f"Service initialization failed: {initialization_error}"
        )
    
    if not chroma_client or not collection or not embedding_model:
        raise HTTPException(
            status_code=503,
            detail="Service dependencies not fully initialized"
        )
    
    try:
        # Quick connection test
        collection.count()
        return {
            "status": "healthy",
            "chromadb_initialized": True,
            "embedding_model_loaded": True
        }
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=f"ChromaDB health check failed: {str(e)}"
        )

class Query(BaseModel):
    question: str

@app.post("/query")
async def query(query: Query):
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
        print(f"Error processing query: {str(e)}")
        print(f"Full traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))

# Add a test endpoint
@app.get("/test")
async def test():
    return {"status": "OK", "message": "API is working"}

@app.get("/db-status")
async def get_db_status():
    try:
        # Get collection info
        results = collection.get()
        
        # Get collection peek
        peek = collection.peek()
        
        return {
            "status": "OK",
            "collection_name": collection.name,
            "document_count": len(results['ids']) if results else 0,
            "has_documents": bool(results and results['ids']),
            "sample_documents": peek['documents'] if peek else [],
            "sample_metadata": peek['metadatas'] if peek else [],
            "db_directory": DB_DIR,
            "directory_contents": os.listdir(DB_DIR) if os.path.exists(DB_DIR) else []
        }
    except Exception as e:
        return {
            "status": "ERROR",
            "error": str(e),
            "traceback": traceback.format_exc()
        }

@app.get("/db-check")
async def check_database():
    try:
        # Get collection info
        results = collection.get()
        
        return {
            "status": "success",
            "total_documents": len(results['ids']) if results['ids'] else 0,
            "sample_metadata": results['metadatas'][:2] if results['metadatas'] else [],
            "sample_text": results['documents'][:1] if results['documents'] else [],
            "total_ids": len(results['ids']) if results['ids'] else 0
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "traceback": traceback.format_exc()
        }

@app.post("/test-query")
async def test_query(query: Query):
    try:
        # Query the collection
        results = collection.query(
            query_texts=[query.question],
            n_results=2
        )
        
        return {
            "status": "success",
            "query": query.question,
            "results": {
                "documents": results['documents'],
                "metadatas": results['metadatas'],
                "distances": results['distances']
            }
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "traceback": traceback.format_exc()
        }
    
@app.get("/debug")
async def debug_database():
    try:
        # Get collection info
        collection_count = len(chroma_client.list_collections())
        collection_info = collection.get()
        
        return {
            "collections_count": collection_count,
            "collection_name": collection.name,
            "document_count": len(collection_info['ids']) if collection_info else 0,
            "has_documents": bool(collection_info and collection_info['ids']),
            "first_few_ids": collection_info['ids'][:5] if collection_info and collection_info['ids'] else [],
            "sample_metadata": collection_info['metadatas'][:2] if collection_info and collection_info['metadatas'] else [],
            "directory_info": {
                "current_dir": os.getcwd(),
                "chroma_dir_exists": os.path.exists("./chroma_db"),
                "chroma_contents": os.listdir("./chroma_db") if os.path.exists("./chroma_db") else []
            }
        }
    except Exception as e:
        return {
            "error": str(e),
            "traceback": traceback.format_exc()
        }

if __name__ == "__main__":
    import uvicorn
    print("\n=== Starting Server ===")
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="debug")