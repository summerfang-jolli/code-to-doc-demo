#!/usr/bin/env python3
"""
Demo script showing how to upload Markdown files to RAGFlow

This script demonstrates the MD upload process and shows discovered files.
"""

import os
import glob
from ragflow_client import RAGFlowClient


def find_and_display_md_files():
    """Find and display all Markdown files in the project"""
    print("🔍 Discovering Markdown files in the project...\n")

    md_files = []
    patterns = ["*.md", "*.markdown"]
    excluded_dirs = ["venv", "node_modules", ".git", "__pycache__", "build", "dist"]

    for pattern in patterns:
        # Current directory
        md_files.extend(glob.glob(pattern))
        # Recursive search
        md_files.extend(glob.glob(f"**/{pattern}", recursive=True))

    # Filter out excluded directories
    filtered_files = []
    for file_path in md_files:
        if not any(excluded_dir in file_path for excluded_dir in excluded_dirs):
            filtered_files.append(file_path)

    # Remove duplicates and sort
    unique_files = sorted(list(set(filtered_files)))

    if unique_files:
        print(f"📝 Found {len(unique_files)} Markdown files:")
        for i, md_file in enumerate(unique_files, 1):
            file_size = os.path.getsize(md_file) if os.path.exists(md_file) else 0
            print(f"  {i:2d}. {md_file}")
            print(f"      Size: {file_size:,} bytes")

            # Show preview of content
            try:
                with open(md_file, 'r', encoding='utf-8') as f:
                    content = f.read(200).strip()
                    preview = content.replace('\n', ' ')
                    if len(content) > 150:
                        preview = preview[:150] + "..."
                    print(f"      Preview: {preview}")
            except Exception as e:
                print(f"      Preview: (Error reading file: {e})")
            print()
    else:
        print("❌ No Markdown files found in the project")

    return unique_files


def demo_md_upload():
    """Demonstrate Markdown file upload to RAGFlow"""
    print("=== RAGFlow Markdown Upload Demo ===\n")

    # Configuration
    api_key = "your-api-key-here"
    base_url = "http://localhost:9380"

    print("📋 Upload Configuration:")
    print(f"🔑 API Key: {api_key[:10]}...")
    print(f"🌐 RAGFlow URL: {base_url}")
    print()

    # Find MD files
    md_files = find_and_display_md_files()

    if md_files:
        # Show API details
        print("🔧 HTTP API Details:")
        print(f"   Method: POST")
        print(f"   URL: {base_url}/api/v1/datasets/{{dataset_id}}/documents")
        print(f"   Headers:")
        print(f"     Authorization: Bearer {api_key[:10]}...")
        print(f"     Content-Type: multipart/form-data")
        print(f"   Body: file (binary content)")
        print()

        # Show usage examples
        print("🚀 Usage Examples:")
        print()

        # Single file examples
        if md_files:
            sample_file = md_files[0]
            print(f"   # Upload single file:")
            print(f"   uv run python upload_md_to_ragflow.py {sample_file}")
            print(f"   uv run python upload_md_to_ragflow.py {sample_file} dataset_123")
            print()

        # Multiple files examples
        print(f"   # Upload all MD files in current directory:")
        print(f"   uv run python upload_md_to_ragflow.py .")
        print(f"   uv run python upload_md_to_ragflow.py . dataset_123")
        print()

        # Directory examples
        print(f"   # Upload all MD files in a specific directory:")
        print(f"   uv run python upload_md_to_ragflow.py docs/")
        print(f"   uv run python upload_md_to_ragflow.py src/ dataset_123")
        print()

        # Show expected processing workflow
        print("🔄 Processing Workflow:")
        print("   1. 📤 File uploaded to RAGFlow dataset")
        print("   2. 🔍 RAGFlow parses and analyzes content")
        print("   3. ✂️  Content is chunked for optimal retrieval")
        print("   4. 🧠 Embeddings generated for semantic search")
        print("   5. 🔎 File becomes searchable in RAG queries")
        print()

        # Show file type benefits
        print("💡 Markdown File Benefits:")
        print("   • Rich formatting preserved (headers, lists, code blocks)")
        print("   • Tables and structured data recognized")
        print("   • Code syntax highlighting maintained")
        print("   • Links and references tracked")
        print("   • Perfect for technical documentation")
        print()

    # Environment setup
    print("📚 Environment Setup:")
    print("   export RAGFLOW_API_KEY=your-actual-api-key")
    print("   export RAGFLOW_BASE_URL=http://localhost:9380  # optional")
    print()

    # Show sample response
    print("✅ Expected Success Response:")
    print("""   {
     "code": 0,
     "message": "success",
     "data": {
       "id": "doc_md_12345",
       "name": "sample.md",
       "status": "uploading",
       "size": 3847
     }
   }""")


if __name__ == "__main__":
    demo_md_upload()