# File: backend/check_database.py

import chromadb
from sentence_transformers import SentenceTransformer
import os

def check_database():
    print("\n=== ChromaDB Check ===")
    DB_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "chroma_db")
    print(f"Database directory: {DB_DIR}")
    
    client = chromadb.PersistentClient(path=DB_DIR)
    collection = client.get_collection("podcast_transcripts")
    
    print("\n=== Collection Contents ===")
    results = collection.get()
    
    print(f"Number of documents: {len(results['ids'])}")
    print(f"Document IDs: {results['ids']}")
    
    if results['documents']:
        print("\n=== First Document Sample ===")
        print(results['documents'][0][:200])
        print("\n=== First Document Metadata ===")
        print(results['metadatas'][0])
    
    print("\n=== Test Query ===")
    # Test query about careers (matching our test document)
    query_result = collection.query(
        query_texts=["Tell me about career framework"],
        n_results=1
    )
    
    print(f"Query found {len(query_result['documents'][0]) if query_result['documents'] else 0} results")
    if query_result['documents'] and query_result['documents'][0]:
        print("\nMatching document:")
        print(query_result['documents'][0][0][:200])
        print("\nMetadata:")
        print(query_result['metadatas'][0])

if __name__ == "__main__":
    check_database()