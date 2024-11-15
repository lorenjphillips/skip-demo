import chromadb
from sentence_transformers import SentenceTransformer
import json

def test_ingestion():
    # Initialize ChromaDB and model
    chroma_client = chromadb.PersistentClient(path="./chroma_db")
    embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
    
    # Delete existing collection if it exists
    try:
        chroma_client.delete_collection("podcast_transcripts")
    except:
        pass
    
    # Create fresh collection
    collection = chroma_client.create_collection("podcast_transcripts")
    
    # Sample episode data
    test_episodes = [
        {
            "episode_id": "ep001",
            "title": "Test Episode 1",
            "content": """Welcome to our first test episode! In this episode, we discuss various topics 
            including artificial intelligence, machine learning, and data science. We explore how these 
            technologies are shaping our future and what it means for everyday life.""",
            "timestamp": "00:00:00"
        },
        {
            "episode_id": "ep002",
            "title": "Test Episode 2",
            "content": """In our second episode, we dive deep into natural language processing and 
            its applications. We discuss how companies are using NLP to improve customer service, 
            analyze social media, and develop better search algorithms.""",
            "timestamp": "00:00:00"
        }
    ]
    
    print("Adding test episodes to database...")
    
    # Add each episode to the collection
    for episode in test_episodes:
        # Generate embeddings
        embeddings = embedding_model.encode([episode["content"]]).tolist()
        
        # Add to ChromaDB
        collection.add(
            embeddings=embeddings,
            documents=[episode["content"]],
            metadatas=[{
                "episode_id": episode["episode_id"],
                "title": episode["title"],
                "timestamp": episode["timestamp"]
            }],
            ids=[episode["episode_id"]]
        )
    
    print("Test data added successfully!")
    
    # Verify the data
    print("\nTesting query...")
    results = collection.query(
        query_texts=["What is discussed in the first episode?"],
        n_results=1
    )
    
    print("\nQuery Results:")
    print(f"Number of documents found: {len(results['documents'])}")
    if results['documents'] and results['documents'][0]:
        print(f"Sample document: {results['documents'][0][0][:200]}...")
        print(f"Metadata: {results['metadatas'][0][0]}")
    
if __name__ == "__main__":
    test_ingestion()