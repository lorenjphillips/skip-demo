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

# Load environment variables
load_dotenv()

# Debug environment setup
print("Starting application...")
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

print("OpenAI API key loaded successfully")

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Initialize OpenAI client
client = OpenAI(api_key=api_key)

# Initialize ChromaDB with a persistent directory
COLLECTION_NAME = "podcast_transcripts"
DB_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "chroma_db")
print(f"Using database directory: {DB_DIR}")

# Create the directory if it doesn't exist
os.makedirs(DB_DIR, exist_ok=True)

# Initialize the client
chroma_client = chromadb.PersistentClient(path=DB_DIR)
print("ChromaDB client initialized")

# Get or create collection function
def get_or_create_collection():
    collections = chroma_client.list_collections()
    for collection in collections:
        if collection.name == COLLECTION_NAME:
            print(f"Found existing collection: {COLLECTION_NAME}")
            return collection
    
    print(f"Creating new collection: {COLLECTION_NAME}")
    return chroma_client.create_collection(name=COLLECTION_NAME)

# Initialize the collection
collection = get_or_create_collection()
print(f"Collection ready: {collection.name}")

# Initialize the embedding model
embedding_model = SentenceTransformer('all-MiniLM-L6-v2')

class Query(BaseModel):
    question: str

@app.get("/test")
async def test_endpoint():
    try:
        # Test the collection
        results = collection.query(
            query_texts=["test"],
            n_results=1
        )
        # Test OpenAI connection
        test_completion = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": "Hello"}]
        )
        return {
            "message": "Backend is running!",
            "collection_name": collection.name,
            "documents_found": len(results['documents'][0]) if results['documents'] else 0,
            "openai_connection": "working"
        }
    except Exception as e:
        return {"error": str(e)}

@app.get("/debug-stats")
async def debug_stats():
    try:
        # Get collection info
        results = collection.get()
        unique_episodes = set()
        for metadata in results['metadatas']:
            if metadata and 'episode_id' in metadata:
                unique_episodes.add(metadata['episode_id'])

        collection_stats = {
            "name": collection.name,
            "total_chunks": len(results['ids']),
            "unique_episodes": len(unique_episodes),
            "episode_ids": list(unique_episodes)
        }
        
        # Get a sample query to show the process
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
        return {"error": str(e)}

@app.post("/query")
async def query_transcripts(query: Query):
    try:
        print(f"Received query: {query.question}")
        print(f"Using collection: {collection.name}")
        
        # Query the collection
        results = collection.query(
            query_texts=[query.question],
            n_results=2
        )
        
        print(f"Found {len(results['documents'])} results")
        
        if not results['documents'] or not results['documents'][0]:
            return JSONResponse(content={
                "answer": "I couldn't find any relevant information in the podcast transcripts.",
                "sources": []
            })

        # Prepare context from relevant transcripts
        context = "\n".join(results['documents'][0])
        
        # Generate response using OpenAI with new client syntax
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
        
        # Access the response content
        answer = completion.choices[0].message.content
        
        # Prepare sources with URLs
        sources = [
            {
                "episode_id": meta['episode_id'],
                "title": meta['title'],
                "url": meta.get('url', '')  # Get URL from metadata if it exists
            }
            for meta in results['metadatas'][0]
        ]
        
        # Remove duplicate sources while preserving order
        seen = set()
        unique_sources = []
        for source in sources:
            if source['episode_id'] not in seen:
                seen.add(source['episode_id'])
                unique_sources.append(source)
        
        return JSONResponse(content={
            "answer": answer,
            "sources": unique_sources
        })
    except Exception as e:
        print(f"Error in query_transcripts: {str(e)}")
        import traceback
        traceback_str = traceback.format_exc()
        print(f"Traceback: {traceback_str}")
        return JSONResponse(
            status_code=500,
            content={"detail": str(e)}
        )

# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": "1.0.0"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="debug")