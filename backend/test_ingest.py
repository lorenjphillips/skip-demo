# File: backend/test_ingest.py

import chromadb
from sentence_transformers import SentenceTransformer
import os

def ingest_test_data():
    print("\n=== Starting Test Ingestion ===")
    DB_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "chroma_db")
    client = chromadb.PersistentClient(path=DB_DIR)
    
    # Delete existing collection if it exists
    try:
        client.delete_collection("podcast_transcripts")
        print("Deleted existing collection")
    except:
        print("No existing collection to delete")
    
    # Create fresh collection
    collection = client.create_collection("podcast_transcripts")
    print("Created new collection")
    
    # Test data
    test_documents = [
        {
            "id": "ep001",
            "content": """In this episode about crafting a career framework, Nikhyl discusses the importance 
            of making deliberate career choices. He emphasizes five key questions that professionals should 
            ask themselves when evaluating career moves. The discussion covers topics like understanding 
            your strengths, identifying growth opportunities, and aligning your career with long-term goals.
            Key points include: 1) Assessing current skills and capabilities, 2) Identifying areas for growth,
            3) Understanding industry trends, 4) Evaluating company culture fit, and 5) Setting clear career objectives.""",
            "metadata": {
                "episode_id": "ep001",
                "title": "Episode 1: Crafting a career framework",
                "url": "https://www.youtube.com/watch?v=ZoAwJxx9me0"
            }
        }
    ]
    
    # Initialize embedding model
    embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
    print("Initialized embedding model")
    
    # Add documents
    for doc in test_documents:
        embeddings = embedding_model.encode([doc['content']]).tolist()
        
        collection.add(
            embeddings=embeddings,
            documents=[doc['content']],
            metadatas=[doc['metadata']],
            ids=[doc['id']]
        )
        print(f"Added document: {doc['id']}")
    
    # Verify ingestion
    results = collection.get()
    print(f"\nVerification:")
    print(f"Documents in collection: {len(results['ids'])}")
    print(f"First document ID: {results['ids'][0]}")

if __name__ == "__main__":
    ingest_test_data()