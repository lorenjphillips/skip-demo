import chromadb
from sentence_transformers import SentenceTransformer
import os

def ingest_test_data():
    # Initialize ChromaDB
    DB_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "chroma_db")
    client = chromadb.PersistentClient(path=DB_DIR)
    
    # Create or get collection
    collection_name = "podcast_transcripts"
    try:
        collection = client.get_collection(collection_name)
        print(f"Found existing collection: {collection_name}")
    except:
        collection = client.create_collection(collection_name)
        print(f"Created new collection: {collection_name}")
    
    # Test data
    test_documents = [
        {
            "id": "ep001",
            "content": """In this episode about crafting a career framework, Nikhyl discusses the importance 
            of making deliberate career choices. He emphasizes five key questions that professionals should 
            ask themselves when evaluating career moves. The discussion covers topics like understanding 
            your strengths, identifying growth opportunities, and aligning your career with long-term goals.""",
            "metadata": {
                "episode_id": "ep001",
                "title": "Episode 1: Crafting a career framework",
                "url": "https://www.youtube.com/watch?v=ZoAwJxx9me0"
            }
        },
        # Add more test episodes as needed
    ]
    
    # Initialize embedding model
    embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
    
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

if __name__ == "__main__":
    ingest_test_data()