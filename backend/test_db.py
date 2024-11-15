import chromadb

def test_database():
    # Initialize ChromaDB
    chroma_client = chromadb.PersistentClient(path="./chroma_db")
    try:
        collection = chroma_client.get_collection("podcast_transcripts")
        
        # Try to get all IDs
        results = collection.query(
            query_embeddings=[[0.0] * 384],  # Default embedding dimension
            n_results=1
        )
        
        print("Collection exists and contains data:")
        print(f"Number of documents found: {len(results['documents'])}")
        if results['documents']:
            print("Sample document:", results['documents'][0][0][:200] + "...")
        
    except Exception as e:
        print(f"Error accessing database: {str(e)}")

if __name__ == "__main__":
    test_database()