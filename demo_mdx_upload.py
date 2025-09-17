#!/usr/bin/env python3
"""
Demo script showing how to upload MDX files to RAGFlow

This script demonstrates the upload process without requiring a live server.
"""

import os
from ragflow_client import RAGFlowClient


def demo_mdx_upload():
    """Demonstrate MDX file upload to RAGFlow"""
    print("=== RAGFlow MDX Upload Demo ===\n")

    # Example configuration
    mdx_file = "sample.mdx"
    api_key = "your-api-key-here"
    base_url = "http://localhost:9380"

    print("📋 Upload Process:")
    print(f"1. 📁 MDX File: {mdx_file}")
    print(f"2. 🔑 API Key: {api_key[:10]}...")
    print(f"3. 🌐 RAGFlow URL: {base_url}")

    # Show the upload API call that would be made
    print("\n🔧 HTTP API Call Details:")
    print(f"   Method: POST")
    print(f"   URL: {base_url}/api/v1/datasets/{{dataset_id}}/documents")
    print(f"   Headers:")
    print(f"     Authorization: Bearer {api_key[:10]}...")
    print(f"   Body: multipart/form-data")
    print(f"     file: {mdx_file} (binary content)")

    # Show expected response
    print("\n✅ Expected Success Response:")
    print("""   {
     "code": 0,
     "message": "success",
     "data": {
       "id": "doc_12345",
       "name": "sample.mdx",
       "status": "uploading"
     }
   }""")

    print("\n🔄 After Upload Steps:")
    print("   1. File gets processed and parsed")
    print("   2. Content is chunked for vector search")
    print("   3. Embeddings are generated")
    print("   4. File becomes searchable in RAG queries")

    # Show usage examples
    print(f"\n🚀 Usage Examples:")
    print(f"   # Upload with existing dataset ID")
    print(f"   python upload_mdx_to_ragflow.py {mdx_file} dataset_123")
    print(f"")
    print(f"   # Interactive mode (select/create dataset)")
    print(f"   python upload_mdx_to_ragflow.py {mdx_file}")

    # Check if sample file exists
    if os.path.exists(mdx_file):
        print(f"\n✅ Sample MDX file '{mdx_file}' is ready for upload!")
        with open(mdx_file, 'r') as f:
            content = f.read()
            print(f"   File size: {len(content)} characters")
            print(f"   Preview: {content[:100]}...")
    else:
        print(f"\n❌ Sample MDX file '{mdx_file}' not found")

    print(f"\n📚 Required Environment Variables:")
    print(f"   export RAGFLOW_API_KEY=your-actual-api-key")
    print(f"   export RAGFLOW_BASE_URL=http://localhost:9380  # optional")


if __name__ == "__main__":
    demo_mdx_upload()