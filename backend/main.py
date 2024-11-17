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

CORS_ORIGINS = [
    "http://localhost:3000",
    "https://skip-demo-47sqo5zkn-lorenphillips-protonmailcs-projects.vercel.app",
    "https://theskipai.com",
    "https://*.vercel.app",  # Allow all Vercel preview deployments
    "*"  # Temporarily allow all origins for debugging
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],  # Changed from specific methods to all
    allow_headers=["*"],
    expose_headers=["*"]
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

if __name__ == "__main__":
    import uvicorn
    print("\n=== Starting Server ===")
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="debug")