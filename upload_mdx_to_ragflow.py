#!/usr/bin/env python3
"""
Upload MDX file to RAGFlow using HTTP API

This script demonstrates how to upload an MDX file to a RAGFlow dataset
using the existing RAGFlowClient.
"""

import os
import sys
from dotenv import load_dotenv
from ragflow_client import RAGFlowClient


def upload_mdx_file(client: RAGFlowClient, dataset_id: str, mdx_file_path: str):
    """
    Upload an MDX file to a RAGFlow dataset

    Args:
        client: RAGFlowClient instance
        dataset_id: Target dataset ID
        mdx_file_path: Path to the MDX file to upload
    """
    print(f"📤 Uploading MDX file: {mdx_file_path}")
    print(f"📂 Target dataset ID: {dataset_id}")

    # Check if file exists
    if not os.path.exists(mdx_file_path):
        print(f"❌ Error: File not found: {mdx_file_path}")
        return None

    # Upload the file
    result = client.upload_file_to_dataset(dataset_id, mdx_file_path)

    if result:
        print("✅ File uploaded successfully!")
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
        print("❌ Failed to upload file")
        return None


def main():
    """Main function to upload MDX file to RAGFlow"""
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

    # Get command line arguments
    if len(sys.argv) < 2:
        print("Usage: python upload_mdx_to_ragflow.py <mdx_file_path> [dataset_id]")
        print("\nExample:")
        print("  python upload_mdx_to_ragflow.py sample.mdx")
        print("  python upload_mdx_to_ragflow.py sample.mdx dataset_123")
        return

    mdx_file_path = sys.argv[1]
    dataset_id = sys.argv[2] if len(sys.argv) > 2 else None

    print("=== RAGFlow MDX Upload ===\n")
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

    # Upload the MDX file
    result = upload_mdx_file(client, dataset_id, mdx_file_path)

    if result:
        # Handle the case where result might be a list or dict
        file_obj = result
        if isinstance(result, list) and len(result) > 0:
            file_obj = result[0]

        file_id = file_obj.get('id') if isinstance(file_obj, dict) else None
        if file_id:
            print(f"\n🔄 Starting file parsing...")
            print(f"📄 File ID: {file_id}")

            # Start parsing the uploaded file
            parsing_result = client.start_file_parsing(dataset_id, file_id)
            if parsing_result:
                print("✅ File parsing started successfully!")
                print(f"📄 Parsing result: {parsing_result}")
            else:
                print("⚠️ File uploaded but parsing may not have started")
        else:
            print("⚠️ Could not extract file ID from upload result")

        # List files in the dataset to confirm upload
        print(f"\n📋 Files in dataset {dataset_id}:")
        files = client.list_dataset_files(dataset_id)
        if files:
            for file_info in files:
                file_name = file_info.get('name', 'Unknown')
                file_status = file_info.get('status', 'Unknown')
                print(f"  - {file_name} (Status: {file_status})")
        else:
            print("  No files found or error retrieving files")


if __name__ == "__main__":
    main()