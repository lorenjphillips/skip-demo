if __name__ == "__main__":
    try:
        print("\n=== Starting Ingest Process ===")
        
        # Debug current environment
        cwd = os.getcwd()
        print(f"\nCurrent working directory: {cwd}")
        print("\nDirectory contents:")
        for item in os.listdir(cwd):
            print(f"  - {item}")
        
        # Check data directory
        data_dir = os.path.join(cwd, "data")
        print(f"\nChecking data directory: {data_dir}")
        if not os.path.exists(data_dir):
            print("ERROR: Data directory not found!")
            sys.exit(1)
        
        # Check transcripts directory
        transcripts_dir = os.path.join(data_dir, "transcripts")
        print(f"\nChecking transcripts directory: {transcripts_dir}")
        if not os.path.exists(transcripts_dir):
            print("ERROR: Transcripts directory not found!")
            sys.exit(1)
            
        print("\nTranscripts directory contents:")
        transcript_files = os.listdir(transcripts_dir)
        for file in transcript_files:
            print(f"  - {file}")
        
        # Check metadata file
        metadata_path = os.path.join(data_dir, "metadata.json")
        print(f"\nChecking metadata file: {metadata_path}")
        if not os.path.exists(metadata_path):
            print("ERROR: Metadata file not found!")
            sys.exit(1)
            
        # Try to read metadata file
        print("\nReading metadata file...")
        with open(metadata_path, 'r') as f:
            metadata = json.load(f)
            print(f"Metadata contains {len(metadata)} entries")
        
        print("\nStarting ingestion process...")
        process_all_episodes(
            transcripts_dir=transcripts_dir,
            metadata_path=metadata_path,
            replace_existing=True
        )
        
        # Verify ingestion
        print("\n=== Verifying Ingestion ===")
        ingestion = PodcastIngestion()
        results = ingestion.collection.get()
        print(f"Documents in collection after ingestion: {len(results['ids']) if results else 0}")
        
        print("\nIngestion completed successfully!")
        
    except Exception as e:
        print(f"\nFATAL ERROR: {str(e)}")
        print(f"\nFull traceback:\n{traceback.format_exc()}")
        sys.exit(1)