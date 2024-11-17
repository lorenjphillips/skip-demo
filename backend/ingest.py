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

class PodcastIngestion:
    def __init__(self, db_path: str = "./chroma_db"):
        """Initialize the ingestion system with ChromaDB and the embedding model."""
        self.chroma_client = chromadb.PersistentClient(path=db_path)
        self.collection = self.get_or_create_collection()
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
    
    def get_or_create_collection(self):
        """Get existing collection or create a new one."""
        try:
            collection = self.chroma_client.get_collection("podcast_transcripts")
            print("Found existing collection")
            return collection
        except:
            print("Creating new collection")
            return self.chroma_client.create_collection("podcast_transcripts")

    def list_existing_episodes(self) -> set:
        """Get a set of episode IDs already in the database."""
        try:
            results = self.collection.get()
            episodes = set()
            for metadata in results['metadatas']:
                if metadata:
                    episodes.add(metadata['episode_id'])
            return episodes
        except Exception as e:
            print(f"Error getting existing episodes: {e}")
            return set()

    def chunk_transcript(self, transcript: str, chunk_size: int = 1000, overlap: int = 100) -> List[str]:
        """Split transcript into overlapping chunks for better context preservation."""
        words = transcript.split()
        chunks = []
        
        for i in range(0, len(words), chunk_size - overlap):
            chunk = " ".join(words[i:i + chunk_size])
            chunks.append(chunk)
        
        return chunks

    def process_episode(self, 
                       episode_id: str, 
                       transcript: str, 
                       title: str, 
                       description: str = "",
                       url: str = "",
                       replace_existing: bool = False) -> None:
        """Process a single episode and add it to the database."""
        
        # Check if episode exists
        existing_episodes = self.list_existing_episodes()
        if episode_id in existing_episodes and not replace_existing:
            print(f"Episode {episode_id} already exists. Skipping...")
            return
        elif episode_id in existing_episodes:
            print(f"Episode {episode_id} exists. Replacing...")
            # Delete existing chunks for this episode
            try:
                results = self.collection.get()
                for i, metadata in enumerate(results['metadatas']):
                    if metadata and metadata['episode_id'] == episode_id:
                        self.collection.delete(ids=[results['ids'][i]])
            except Exception as e:
                print(f"Error deleting existing episode: {e}")
        
        # Combine description with transcript for better context
        full_content = f"Episode Title: {title}\nDescription: {description}\nTranscript: {transcript}"
        
        # Chunk the content
        chunks = self.chunk_transcript(full_content)
        
        print(f"Processing episode {episode_id}: {title}")
        print(f"Created {len(chunks)} chunks")
        
        # Process each chunk
        for idx, chunk in enumerate(chunks):
            chunk_id = f"{episode_id}_chunk_{idx}"
            
            # Generate embeddings
            embeddings = self.embedding_model.encode([chunk]).tolist()
            
            # Prepare metadata
            metadata = {
                "episode_id": episode_id,
                "title": title,
                "chunk_index": idx,
                "total_chunks": len(chunks),
                "description": description[:200] + "..." if description else "",
                "url": url  
            }
            
            # Add to ChromaDB
            self.collection.add(
                embeddings=embeddings,
                documents=[chunk],
                metadatas=[metadata],
                ids=[chunk_id]
            )
            
            if idx % 10 == 0:  # Progress indicator
                print(f"Processed chunk {idx + 1}/{len(chunks)}")

def process_all_episodes(
    transcripts_dir: str, 
    metadata_path: str, 
    replace_existing: bool = False,
    specific_episodes: List[str] = None
):
    """
    Process episodes from the transcripts directory.
    
    Args:
        transcripts_dir: Directory containing transcript files
        metadata_path: Path to metadata JSON file
        replace_existing: Whether to replace existing episodes
        specific_episodes: List of episode IDs to process (None for all)
    """
    # Initialize ingestion system
    ingestion = PodcastIngestion()
    
    # Show existing episodes
    existing_episodes = ingestion.list_existing_episodes()
    print(f"\nExisting episodes in database: {existing_episodes}\n")
    
    # Load metadata
    with open(metadata_path, 'r') as f:
        metadata = json.load(f)
    
    # Process each transcript file
    for filename in os.listdir(transcripts_dir):
        if filename.endswith('.txt'):
            episode_id = filename.split('.')[0]  # episode_001 -> episode_001
            
            # Skip if not in specific episodes list
            if specific_episodes and episode_id not in specific_episodes:
                continue
            
            # Get metadata for this episode
            episode_meta = metadata.get(episode_id, {})
            if not episode_meta:
                print(f"Warning: No metadata found for {episode_id}")
                continue
            
            # Read transcript
            with open(os.path.join(transcripts_dir, filename), 'r') as f:
                transcript = f.read()
            
            # Process episode
            ingestion.process_episode(
                episode_id=episode_id,
                transcript=transcript,
                title=episode_meta.get('title', f'Episode {episode_id}'),
                description=episode_meta.get('description', ''),
                replace_existing=replace_existing
            )
            
            print(f"Completed processing {episode_id}")

# Main execution
if __name__ == "__main__":
    import os
    
    # Debug: Print current directory and contents
    print(f"Current working directory: {os.getcwd()}")
    print(f"Directory contents: {os.listdir()}")
    
    # Make paths absolute
    base_dir = os.path.dirname(os.path.abspath(__file__))
    transcripts_dir = os.path.join(base_dir, "data", "transcripts")
    metadata_path = os.path.join(base_dir, "data", "metadata.json")
    
    # Debug: Print paths and existence
    print(f"Base directory: {base_dir}")
    print(f"Transcripts directory: {transcripts_dir}")
    print(f"Metadata path: {metadata_path}")
    print(f"Transcripts directory exists: {os.path.exists(transcripts_dir)}")
    print(f"Metadata file exists: {os.path.exists(metadata_path)}")
    
    try:
        print("\nStarting podcast transcript processing...")
        process_all_episodes(
            transcripts_dir=transcripts_dir,
            metadata_path=metadata_path,
            replace_existing=True  # Always replace existing episodes
        )
        print("\nProcessing completed successfully")
    except Exception as e:
        print(f"Error during processing: {str(e)}")
        import traceback
        print(f"Full traceback: {traceback.format_exc()}")
        exit(1)