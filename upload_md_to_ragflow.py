#!/usr/bin/env python3
"""
Upload Markdown (.md) file to RAGFlow using HTTP API

This script demonstrates how to upload Markdown files to a RAGFlow dataset
for document processing and semantic search capabilities.
"""

import os
import sys
import glob
from typing import List
from dotenv import load_dotenv
from ragflow_client import RAGFlowClient


def find_md_files(directory: str = ".") -> List[str]:
    """
    Find all Markdown files in the specified directory

    Args:
        directory: Directory to search for MD files

    Returns:
        List of MD file paths
    """
    md_files = []
    for pattern in ["*.md", "*.markdown"]:
        md_files.extend(glob.glob(os.path.join(directory, pattern)))
        md_files.extend(glob.glob(os.path.join(directory, "**", pattern), recursive=True))

    # Filter out files in virtual environments and other common exclusions
    excluded_dirs = ["venv", "node_modules", ".git", "__pycache__", "build", "dist"]
    filtered_files = []
    for file_path in md_files:
        if not any(excluded_dir in file_path for excluded_dir in excluded_dirs):
            filtered_files.append(file_path)

    return sorted(list(set(filtered_files)))


def upload_md_file(client: RAGFlowClient, dataset_id: str, md_file_path: str):
    """
    Upload a Markdown file to a RAGFlow dataset

    Args:
        client: RAGFlowClient instance
        dataset_id: Target dataset ID
        md_file_path: Path to the MD file to upload
    """
    print(f"📤 Uploading Markdown file: {md_file_path}")
    print(f"📂 Target dataset ID: {dataset_id}")

    # Check if file exists
    if not os.path.exists(md_file_path):
        print(f"❌ Error: File not found: {md_file_path}")
        return None

    # Get file size for display
    file_size = os.path.getsize(md_file_path)
    print(f"📏 File size: {file_size} bytes")

    # Upload the file
    result = client.upload_file_to_dataset(dataset_id, md_file_path)

    if result:
        print("✅ Markdown file uploaded successfully!")
        print(f"📄 Upload result: {result}")
        # Handle the case where result is a list (which RAGFlow returns)
        if isinstance(result, list) and len(result) > 0:
            return result[0]  # Return the first uploaded file
        elif isinstance(result, dict):
            return result
        else:
            print("⚠️ Unexpected result format")
            return result
    else:
        print("❌ Failed to upload Markdown file")
        return None


def upload_multiple_md_files(client: RAGFlowClient, dataset_id: str, md_files: List[str]):
    """
    Upload multiple Markdown files to a RAGFlow dataset

    Args:
        client: RAGFlowClient instance
        dataset_id: Target dataset ID
        md_files: List of MD file paths to upload
    """
    print(f"📚 Uploading {len(md_files)} Markdown files to dataset {dataset_id}")

    successful_uploads = []
    failed_uploads = []

    for i, md_file in enumerate(md_files, 1):
        print(f"\n[{i}/{len(md_files)}] Processing: {md_file}")
        result = upload_md_file(client, dataset_id, md_file)

        if result:
            successful_uploads.append(md_file)
            # Start parsing for each uploaded file
            # Handle the case where result might be a list or dict
            file_obj = result
            if isinstance(result, list) and len(result) > 0:
                file_obj = result[0]

            file_id = file_obj.get('id') if isinstance(file_obj, dict) else None
            if file_id:
                print(f"🔄 Starting parsing for {os.path.basename(md_file)}...")
                parsing_result = client.start_file_parsing(dataset_id, file_id)
                if parsing_result:
                    print("✅ Parsing started successfully")
                else:
                    print("⚠️ Parsing may not have started properly")
            else:
                print("⚠️ Could not extract file ID from result")
        else:
            failed_uploads.append(md_file)

    # Summary
    print(f"\n📊 Upload Summary:")
    print(f"   ✅ Successful: {len(successful_uploads)}")
    print(f"   ❌ Failed: {len(failed_uploads)}")

    if failed_uploads:
        print(f"\n❌ Failed uploads:")
        for file_path in failed_uploads:
            print(f"   - {file_path}")


def main():
    """Main function to upload Markdown files to RAGFlow"""
    # Load environment variables
    load_dotenv()

    # Get API key
    API_KEY = os.getenv("RAGFLOW_API_KEY")
    if not API_KEY:
        print("❌ Error: RAGFLOW_API_KEY not found in environment variables")
        print("\nPlease set your API key:")
        print("export RAGFLOW_API_KEY=your-api-key-here")
        return

    # Get base URL
    BASE_URL = os.getenv("RAGFLOW_BASE_URL", "http://localhost:9380")

    # Parse command line arguments
    if len(sys.argv) < 2:
        print("Usage: python upload_md_to_ragflow.py <md_file_or_directory> [dataset_id]")
        print("\nExamples:")
        print("  python upload_md_to_ragflow.py sample.md")
        print("  python upload_md_to_ragflow.py sample.md dataset_123")
        print("  python upload_md_to_ragflow.py docs/")
        print("  python upload_md_to_ragflow.py . dataset_123  # Upload all MD files in current dir")
        return

    file_or_dir = sys.argv[1]
    dataset_id = sys.argv[2] if len(sys.argv) > 2 else None

    print("=== RAGFlow Markdown Upload ===\n")
    print(f"📍 Connecting to: {BASE_URL}")

    # Initialize client
    client = RAGFlowClient(API_KEY, BASE_URL)

    # Test connection
    print("🔌 Testing connection...")
    if not client.test_connection():
        print("❌ Failed to connect to RAGFlow server")
        print("Make sure RAGFlow is running on localhost:9380")
        return
    print("✅ Connected successfully!")

    # Determine what to upload
    md_files = []
    if os.path.isfile(file_or_dir):
        if file_or_dir.endswith(('.md', '.markdown')):
            md_files = [file_or_dir]
        else:
            print(f"❌ Error: {file_or_dir} is not a Markdown file")
            return
    elif os.path.isdir(file_or_dir):
        print(f"🔍 Searching for Markdown files in: {file_or_dir}")
        md_files = find_md_files(file_or_dir)
        if not md_files:
            print(f"❌ No Markdown files found in {file_or_dir}")
            return
        print(f"📝 Found {len(md_files)} Markdown files:")
        for md_file in md_files:
            print(f"   - {md_file}")
    else:
        print(f"❌ Error: {file_or_dir} does not exist")
        return

    # If no dataset_id provided, list available datasets
    if not dataset_id:
        print("\n📚 Available datasets:")
        datasets = client.list_datasets()
        if datasets:
            for i, dataset in enumerate(datasets):
                print(f"  {i+1}. {dataset.get('name', 'Unnamed')} (ID: {dataset.get('id')})")
                print(f"     Description: {dataset.get('description', 'No description')}")

            # Ask user to select a dataset
            try:
                choice = input("\nEnter dataset number (or 'new' to create new): ").strip()
                if choice.lower() == 'new':
                    # Create new dataset
                    name = input("Enter new dataset name: ").strip()
                    description = input("Enter description (optional): ").strip()
                    new_dataset = client.create_dataset(name, description)
                    if new_dataset:
                        dataset_id = new_dataset.get('id')
                        print(f"✅ Created new dataset: {name} (ID: {dataset_id})")
                    else:
                        print("❌ Failed to create dataset")
                        return
                else:
                    choice_idx = int(choice) - 1
                    if 0 <= choice_idx < len(datasets):
                        dataset_id = datasets[choice_idx].get('id')
                        print(f"📂 Selected dataset: {datasets[choice_idx].get('name')} (ID: {dataset_id})")
                    else:
                        print("❌ Invalid choice")
                        return
            except (ValueError, KeyboardInterrupt):
                print("\n❌ Operation cancelled")
                return
        else:
            print("  No datasets found. Creating a new one...")
            name = input("Enter new dataset name: ").strip()
            description = input("Enter description (optional): ").strip()
            new_dataset = client.create_dataset(name, description)
            if new_dataset:
                dataset_id = new_dataset.get('id')
                print(f"✅ Created new dataset: {name} (ID: {dataset_id})")
            else:
                print("❌ Failed to create dataset")
                return

    # Upload the Markdown files
    if len(md_files) == 1:
        # Single file upload
        result = upload_md_file(client, dataset_id, md_files[0])
        if result:
            # Handle the case where result might be a list or dict
            file_obj = result
            if isinstance(result, list) and len(result) > 0:
                file_obj = result[0]

            file_id = file_obj.get('id') if isinstance(file_obj, dict) else None
            if file_id:
                print(f"\n🔄 Starting file parsing...")
                parsing_result = client.start_file_parsing(dataset_id, file_id)
                if parsing_result:
                    print("✅ File parsing started successfully!")
                    print(f"📄 File ID: {file_id}")
                else:
                    print("⚠️ File uploaded but parsing may not have started")
            else:
                print("⚠️ Could not extract file ID from upload result")
    else:
        # Multiple files upload
        upload_multiple_md_files(client, dataset_id, md_files)

    # List files in the dataset to confirm uploads
    print(f"\n📋 Files in dataset {dataset_id}:")
    files = client.list_dataset_files(dataset_id)
    if files:
        for file_info in files:
            file_name = file_info.get('name', 'Unknown')
            file_status = file_info.get('status', 'Unknown')
            file_size = file_info.get('size', 'Unknown')
            print(f"  - {file_name} (Status: {file_status}, Size: {file_size})")
    else:
        print("  No files found or error retrieving files")

    print(f"\n🎉 Upload process completed!")


if __name__ == "__main__":
    main()