import chromadb

def check_collection():
    client = chromadb.PersistentClient(path="./chroma_db")
    
    # List all collections
    print("Available collections:")
    print(client.list_collections())
    
    try:
        collection = client.get_collection("podcast_transcripts")
        
        # Get a sample query
        results = collection.query(
            query_texts=["test"],
            n_results=1
        )
        
        print("\nCollection contents:")
        print(f"Documents found: {len(results['documents'])}")
        if results['documents'] and results['documents'][0]:
            print(f"Sample document: {results['documents'][0][0][:200]}...")
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    check_collection()