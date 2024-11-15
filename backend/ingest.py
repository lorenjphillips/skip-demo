import json
import os
from typing import List, Dict
import chromadb
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv

class PodcastIngestion:
    def __init__(self, db_path: str = "./chroma_db"):
        """Initialize the ingestion system with ChromaDB and the embedding model."""
        self.chroma_client = chromadb.PersistentClient(path=db_path)
        try:
            self.collection = self.chroma_client.create_collection("podcast_transcripts")
        except:
            self.collection = self.chroma_client.get_collection("podcast_transcripts")
        
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
    
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
                       timestamps: Dict[str, str] = None) -> None:
        """Process a single episode and add it to the database."""
        
        # Combine description with transcript for better context
        full_content = f"Episode Title: {title}\nDescription: {description}\nTranscript: {transcript}"
        
        # Chunk the content
        chunks = self.chunk_transcript(full_content)
        
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
                "description": description[:200] + "..." if description else "",  # Store truncated description
            }
            
            # Add timestamp if available
            if timestamps and str(idx) in timestamps:
                metadata["timestamp"] = timestamps[str(idx)]
            
            # Add to ChromaDB
            self.collection.add(
                embeddings=embeddings,
                documents=[chunk],
                metadatas=[metadata],
                ids=[chunk_id]
            )
    
    def ingest_from_json(self, json_path: str) -> None:
        """Ingest episodes from a JSON file."""
        with open(json_path, 'r') as f:
            episodes = json.load(f)
        
        for episode in episodes:
            self.process_episode(
                episode_id=episode["episode_id"],
                transcript=episode["transcript"],
                title=episode["title"],
                description=episode.get("description", ""),
                timestamps=episode.get("timestamps", {})
            )

    def clear_database(self) -> None:
        """Clear all data from the database."""
        self.chroma_client.delete_collection("podcast_transcripts")
        self.collection = self.chroma_client.create_collection("podcast_transcripts")

if __name__ == "__main__":
    # Example usage
    ingestion = PodcastIngestion()
    
    # Example of direct episode ingestion
    '''
    ingestion.process_episode(
        episode_id="ep1",
        transcript="Your transcript text here...",
        title="Episode 1: Introduction",
        description="In this episode...",
        timestamps={"0": "00:00:00", "1": "00:05:30"}
    )
    '''
    
    # Example of JSON file ingestion
    # ingestion.ingest_from_json("episodes.json")