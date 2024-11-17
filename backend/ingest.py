if __name__ == "__main__":
    import os
    import sys
    
    try:
        # Debug: Print current directory and contents
        cwd = os.getcwd()
        print(f"Current working directory: {cwd}")
        print("Contents of current directory:")
        for item in os.listdir(cwd):
            print(f"  - {item}")
        
        # Check data directory
        data_dir = os.path.join(cwd, "data")
        if not os.path.exists(data_dir):
            print(f"ERROR: Data directory not found at {data_dir}")
            sys.exit(1)
            
        # Check transcripts directory
        transcripts_dir = os.path.join(data_dir, "transcripts")
        if not os.path.exists(transcripts_dir):
            print(f"ERROR: Transcripts directory not found at {transcripts_dir}")
            sys.exit(1)
            
        # Check metadata file
        metadata_path = os.path.join(data_dir, "metadata.json")
        if not os.path.exists(metadata_path):
            print(f"ERROR: Metadata file not found at {metadata_path}")
            sys.exit(1)
            
        print("\nAll required files and directories found!")
        print(f"Contents of transcripts directory:")
        for item in os.listdir(transcripts_dir):
            print(f"  - {item}")
            
        print("\nStarting podcast transcript processing...")
        process_all_episodes(
            transcripts_dir=transcripts_dir,
            metadata_path=metadata_path,
            replace_existing=True
        )
        print("\nProcessing completed successfully")
        
    except Exception as e:
        print(f"\nFATAL ERROR: {str(e)}")
        import traceback
        print(f"\nFull traceback:\n{traceback.format_exc()}")
        sys.exit(1)