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
                {"role": "system", "content": "You are a helpful assistant that answers questions about podcast episodes. Always cite the episode title in your response."},
                {"role": "user", "content": f"Context from podcast transcripts:\n{context}\n\nQuestion: {query.question}"}
            ]
        )
        
        # Access the response content using new syntax
        answer = completion.choices[0].message.content
        
        return JSONResponse(content={
            "answer": answer,
            "sources": [
                {
                    "episode_id": results['metadatas'][0][i]['episode_id'],
                    "title": results['metadatas'][0][i]['title'],
                    "timestamp": results['metadatas'][0][i]['timestamp']
                }
                for i in range(len(results['metadatas'][0]))
            ]
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="debug")