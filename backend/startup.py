# startup.py
import os
import chromadb
from ingest import process_all_episodes

def ensure_data_loaded():
    client = chromadb.PersistentClient(path="/data/chroma_db")
    try:
        collection = client.get_collection("podcast_transcripts")
        count = collection.count()
        print(f"Found {count} documents in collection")
        
        if count == 0:
            print("Collection empty, running ingestion...")
            base_dir = os.path.dirname(os.path.abspath(__file__))
            transcripts_dir = os.path.join(base_dir, "data", "transcripts")
            metadata_path = os.path.join(base_dir, "data", "metadata.json")
            
            process_all_episodes(
                transcripts_dir=transcripts_dir,
                metadata_path=metadata_path,
                replace_existing=True
            )
            print("Ingestion complete")
    except Exception as e:
        print(f"Error checking/loading data: {e}")
        raise

if __name__ == "__main__":
    ensure_data_loaded()