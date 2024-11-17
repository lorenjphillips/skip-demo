import json
import os
from typing import List, Dict
import chromadb
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv
import sys
import traceback

# All your class definitions and functions here
class PodcastIngestion:
    # Your existing PodcastIngestion class code...
    pass

def process_all_episodes(
    transcripts_dir: str, 
    metadata_path: str, 
    replace_existing: bool = False,
    specific_episodes: List[str] = None
):
    # Your existing process_all_episodes function code...
    pass

# Main execution
if __name__ == "__main__":
    try:
        # Debug: Print current directory and contents
        cwd = os.getcwd()
        print(f"Current working directory: {cwd}")
        print("Contents of current directory:")
        for item in os.listdir(cwd):
            print(f"  - {item}")
        
        # Make paths absolute
        data_dir = os.path.join(cwd, "data")
        transcripts_dir = os.path.join(data_dir, "transcripts")
        metadata_path = os.path.join(data_dir, "metadata.json")
        
        print("\nStarting podcast transcript processing...")
        process_all_episodes(
            transcripts_dir=transcripts_dir,
            metadata_path=metadata_path,
            replace_existing=True
        )
        print("\nProcessing completed successfully")
        
    except Exception as e:
        print(f"\nFATAL ERROR: {str(e)}")
        print(f"\nFull traceback:\n{traceback.format_exc()}")
        sys.exit(1)