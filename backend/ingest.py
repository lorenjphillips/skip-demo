if __name__ == "__main__":
    import argparse
    import os
    
    # Debug: Print current directory and contents
    print(f"Current working directory: {os.getcwd()}")
    print(f"Directory contents: {os.listdir()}")
    
    # Make paths absolute
    base_dir = os.path.dirname(os.path.abspath(__file__))
    transcripts_dir = os.path.join(base_dir, "data", "transcripts")
    metadata_path = os.path.join(base_dir, "data", "metadata.json")
    
    # Debug: Print paths
    print(f"Base directory: {base_dir}")
    print(f"Transcripts directory: {transcripts_dir}")
    print(f"Metadata path: {metadata_path}")
    
    # Check if directories/files exist
    print(f"Transcripts directory exists: {os.path.exists(transcripts_dir)}")
    print(f"Metadata file exists: {os.path.exists(metadata_path)}")
    
    parser = argparse.ArgumentParser(description='Process podcast transcripts')
    parser.add_argument('--replace', action='store_true', help='Replace existing episodes')
    parser.add_argument('--episodes', nargs='+', help='Specific episode IDs to process')
    parser.add_argument('--yes', '-y', action='store_true', help='Skip confirmation prompt')
    
    args = parser.parse_args()
    
    # Show what will happen
    print("\nCurrent configuration:")
    print(f"Replace existing episodes: {args.replace}")
    print(f"Specific episodes to process: {args.episodes or 'All'}\n")
    
    # Skip confirmation if --yes flag is provided
    if args.yes:
        proceed = True
    else:
        confirm = input("Continue with these settings? (y/n): ")
        proceed = confirm.lower() == 'y'
    
    if proceed:
        try:
            process_all_episodes(
                transcripts_dir=transcripts_dir,
                metadata_path=metadata_path,
                replace_existing=args.replace,
                specific_episodes=args.episodes
            )
        except Exception as e:
            print(f"Error during processing: {str(e)}")
            import traceback
            print(f"Full traceback: {traceback.format_exc()}")
            exit(1)
    else:
        print("Aborted.")
        exit(1)