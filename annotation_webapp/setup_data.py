#!/usr/bin/env python3
"""
Setup script for annotation data directory.
Helps copy model JSON files to the annotation_data directory.
"""

import json
import shutil
from pathlib import Path

# Define paths
BASE_DIR = Path(__file__).parent
ANNOTATION_DATA_DIR = BASE_DIR / 'data' / 'annotation_data'
SOURCE_DATA_DIR = BASE_DIR.parent  # Parent of annotation_webapp

def setup_annotation_data():
    """Setup annotation data directory with model JSON files."""
    print("=" * 60)
    print("ASR Annotation Webapp - Data Setup")
    print("=" * 60)
    
    # Ensure directory exists
    ANNOTATION_DATA_DIR.mkdir(parents=True, exist_ok=True)
    print(f"\n✓ Annotation data directory: {ANNOTATION_DATA_DIR}")
    
    # Look for existing JSON files
    print("\nSearching for annotation data files...")
    found_files = []
    
    # Common patterns
    patterns = [
        '*_annotation_data.json',
        'whisper*.json',
        'phi*.json',
        '*asr*.json'
    ]
    
    for pattern in patterns:
        found = list(SOURCE_DATA_DIR.rglob(pattern))
        found_files.extend(found)
    
    # Remove duplicates
    found_files = list(set(found_files))
    
    if not found_files:
        print("⚠️  No annotation data files found!")
        print("\nExpected format: {model_name}_annotation_data.json")
        print("Example: whisper_annotation_data.json")
        print("\nPlease manually copy your JSON files to:")
        print(f"   {ANNOTATION_DATA_DIR}")
        return
    
    print(f"\nFound {len(found_files)} potential data files:")
    for i, file in enumerate(found_files, 1):
        print(f"  {i}. {file.name} ({file.parent.name}/)")
    
    # Interactive copy
    print("\n" + "=" * 60)
    print("Copy files to annotation_data directory")
    print("=" * 60)
    
    copied = 0
    for file in found_files:
        response = input(f"\nCopy {file.name}? (y/n/rename): ").strip().lower()
        
        if response == 'y':
            dest = ANNOTATION_DATA_DIR / file.name
            shutil.copy2(file, dest)
            print(f"  ✓ Copied to {dest.name}")
            copied += 1
        
        elif response == 'rename':
            new_name = input(f"  New name (e.g., whisper_annotation_data.json): ").strip()
            if not new_name.endswith('.json'):
                new_name += '.json'
            
            dest = ANNOTATION_DATA_DIR / new_name
            shutil.copy2(file, dest)
            print(f"  ✓ Copied as {dest.name}")
            copied += 1
    
    print("\n" + "=" * 60)
    print(f"Setup complete! Copied {copied} files.")
    print("=" * 60)
    
    # List final contents
    files_in_dir = list(ANNOTATION_DATA_DIR.glob('*.json'))
    if files_in_dir:
        print(f"\nFiles in annotation_data directory ({len(files_in_dir)}):")
        for file in files_in_dir:
            # Try to get count
            try:
                with open(file) as f:
                    data = json.load(f)
                    count = len(data) if isinstance(data, list) else "?"
                    print(f"  • {file.name} ({count} utterances)")
            except:
                print(f"  • {file.name}")
    else:
        print("\n⚠️  No files in annotation_data directory yet!")
    
    print("\nNext steps:")
    print("  1. Start the Flask app: python app.py")
    print("  2. Login with annotator credentials")
    print("  3. Select a model to annotate")

def validate_json_format(file_path):
    """Validate that JSON file has correct format."""
    try:
        with open(file_path) as f:
            data = json.load(f)
        
        if not isinstance(data, list):
            return False, "Not a list"
        
        if len(data) == 0:
            return False, "Empty list"
        
        # Check first item has required fields
        required = ['utterance_id', 'human_transcript', 'asr_reconstructed']
        first = data[0]
        missing = [f for f in required if f not in first]
        
        if missing:
            return False, f"Missing fields: {', '.join(missing)}"
        
        return True, f"{len(data)} utterances"
    
    except json.JSONDecodeError as e:
        return False, f"Invalid JSON: {e}"
    except Exception as e:
        return False, str(e)

def list_annotation_data():
    """List current annotation data files."""
    files = list(ANNOTATION_DATA_DIR.glob('*.json'))
    
    if not files:
        print("No annotation data files found.")
        return
    
    print(f"\nAnnotation Data Files ({len(files)}):")
    print("=" * 60)
    
    for file in files:
        valid, info = validate_json_format(file)
        status = "✓" if valid else "✗"
        print(f"{status} {file.name}")
        print(f"   {info}")

if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == 'list':
        list_annotation_data()
    else:
        setup_annotation_data()
