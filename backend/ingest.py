if __name__ == "__main__":
    import argparse
    import os
    
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
        process_all_episodes(
            transcripts_dir="./data/transcripts",
            metadata_path="./data/metadata.json",
            replace_existing=args.replace,
            specific_episodes=args.episodes
        )
    else:
        print("Aborted.")
        exit()