"""
Simple RAGFlow Client - Connect to localhost RAGFlow server

This script demonstrates how to connect to a RAGFlow server running on localhost
and perform basic operations like creating datasets and asking questions.
"""

import os
import sys
import requests
import json
from typing import Optional, Dict, List
from dotenv import load_dotenv


class RAGFlowClient:
    """Simple client for connecting to RAGFlow server on localhost"""

    def __init__(self, api_key: str, base_url: str = "http://localhost:9380"):
        """
        Initialize RAGFlow client

        Args:
            api_key: Your RAGFlow API key
            base_url: RAGFlow server URL (default: localhost:9380)
        """
        self.api_key = api_key
        self.base_url = base_url.rstrip('/')
        self.headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.api_key}'
        }

    def test_connection(self) -> bool:
        """Test if we can connect to RAGFlow server"""
        try:
            response = requests.get(f"{self.base_url}/api/v1/health", headers=self.headers, timeout=5)
            return response.status_code == 200
        except requests.exceptions.RequestException:
            return False

    def list_datasets(self) -> Optional[List[Dict]]:
        """List all available datasets"""
        try:
            response = requests.get(f"{self.base_url}/api/v1/datasets", headers=self.headers)
            if response.status_code == 200:
                result = response.json()
                return result.get('data', [])
            else:
                print(f"Error listing datasets: {response.status_code} - {response.text}")
                return None
        except requests.exceptions.RequestException as e:
            print(f"Connection error: {e}")
            return None

    def create_dataset(self, name: str, description: str = "") -> Optional[Dict]:
        """Create a new dataset"""
        data = {
            "name": name,
            "description": description
        }
        try:
            response = requests.post(f"{self.base_url}/api/v1/datasets",
                                   headers=self.headers, json=data)
            if response.status_code in [200, 201]:
                result = response.json()
                # Check if there's an error code in the response
                if result.get('code') == 0:  # Success code
                    return result.get('data')
                else:
                    print(f"API Error: {result.get('message', 'Unknown error')}")
                    return None
            else:
                print(f"Error creating dataset: {response.status_code} - {response.text}")
                return None
        except requests.exceptions.RequestException as e:
            print(f"Connection error: {e}")
            return None

    def list_chats(self) -> Optional[List[Dict]]:
        """List all available chats and their IDs"""
        try:
            response = requests.get(f"{self.base_url}/api/v1/chats", headers=self.headers)
            if response.status_code == 200:
                return response.json().get('data', [])
            else:
                print(f"Error listing chats: {response.status_code} - {response.text}")
                return None
        except requests.exceptions.RequestException as e:
            print(f"Connection error: {e}")
            return None

    def upload_file_to_dataset(self, dataset_id: str, file_path: str) -> Optional[Dict]:
        """Upload a file to a specific dataset"""
        try:
            # Prepare file upload headers (Content-Type is automatically set for multipart/form-data)
            upload_headers = {
                'Authorization': f'Bearer {self.api_key}'
            }

            with open(file_path, 'rb') as file:
                files = {'file': (os.path.basename(file_path), file)}

                # Use the correct endpoint from RAGFlow documentation
                endpoint = f"{self.base_url}/api/v1/datasets/{dataset_id}/documents"

                response = requests.post(
                    endpoint,
                    headers=upload_headers,
                    files=files
                )

                if response.status_code in [200, 201]:
                    result = response.json()
                    # Check if there's an error code in the response
                    if result.get('code') == 0:  # Success code
                        return result.get('data')
                    else:
                        print(f"API Error: {result.get('message', 'Unknown error')}")
                        return None
                else:
                    print(f"Error uploading file: {response.status_code} - {response.text}")
                    return None

        except requests.exceptions.RequestException as e:
            print(f"Connection error: {e}")
            return None
        except FileNotFoundError:
            print(f"File not found: {file_path}")
            return None

    def list_dataset_files(self, dataset_id: str) -> Optional[List[Dict]]:
        """List files in a specific dataset"""
        try:
            # Use documents endpoint instead of files
            response = requests.get(f"{self.base_url}/api/v1/datasets/{dataset_id}/documents", headers=self.headers)
            if response.status_code == 200:
                result = response.json()
                if result.get('code') == 0:
                    data = result.get('data', {})
                    # The API returns data.docs instead of just data
                    if isinstance(data, dict) and 'docs' in data:
                        return data['docs']
                    elif isinstance(data, list):
                        return data
                    else:
                        return []
                else:
                    print(f"API Error: {result.get('message', 'Unknown error')}")
                    return None
            else:
                print(f"Error listing dataset files: {response.status_code} - {response.text}")
                return None
        except requests.exceptions.RequestException as e:
            print(f"Connection error: {e}")
            return None

    def start_file_parsing(self, dataset_id: str, file_id: str) -> Optional[Dict]:
        """Start parsing a file in a dataset using the chunks endpoint"""
        try:
            # Use the correct chunks endpoint for parsing
            endpoint = f"{self.base_url}/api/v1/datasets/{dataset_id}/chunks"
            data = {"document_ids": [file_id]}

            response = requests.post(endpoint, headers=self.headers, json=data)

            if response.status_code in [200, 201]:
                result = response.json()
                if result.get('code') == 0:  # Success
                    # For parsing, the API may just return code:0 without data
                    return result.get('data', result)
                else:
                    print(f"API Error: {result.get('message', 'Unknown error')}")
                    return None
            else:
                print(f"Error starting file parsing: {response.status_code} - {response.text}")
                return None

        except requests.exceptions.RequestException as e:
            print(f"Connection error: {e}")
            return None

    def get_file_parsing_status(self, dataset_id: str, file_id: str) -> Optional[Dict]:
        """Get parsing status of a file"""
        try:
            # Try different possible endpoints for getting document status
            endpoints = [
                f"{self.base_url}/api/v1/datasets/{dataset_id}/documents/{file_id}",
                f"{self.base_url}/api/v1/datasets/{dataset_id}/files/{file_id}/status",
                f"{self.base_url}/api/v1/documents/{file_id}"
            ]

            for endpoint in endpoints:
                response = requests.get(endpoint, headers=self.headers)

                if response.status_code == 200:
                    result = response.json()
                    if result.get('code') == 0:
                        data = result.get('data')
                        if data:
                            return data
                    elif result.get('code') != 100:  # Not a 404-like error
                        print(f"API Error: {result.get('message', 'Unknown error')}")
                        break

            return None
        except requests.exceptions.RequestException as e:
            print(f"Connection error: {e}")
            return None

    def chat_completion(self, chat_id: str, message: str, model: str = "default") -> Optional[str]:
        """Send a chat completion request"""
        url = f"{self.base_url}/api/v1/chats_openai/{chat_id}/chat/completions"
        data = {
            "model": model,
            "messages": [
                {"role": "user", "content": message}
            ],
            "stream": False
        }

        try:
            response = requests.post(url, headers=self.headers, json=data)
            if response.status_code == 200:
                result = response.json()
                return result.get('choices', [{}])[0].get('message', {}).get('content', '')
            else:
                print(f"Error in chat completion: {response.status_code} - {response.text}")
                return None
        except requests.exceptions.RequestException as e:
            print(f"Connection error: {e}")
            return None


def main():
    """Demo the RAGFlow client"""
    # Load environment variables from .env file
    load_dotenv()

    # Get API key from environment variable
    API_KEY = os.getenv("RAGFLOW_API_KEY")

    if not API_KEY:
        print("❌ Error: RAGFLOW_API_KEY not found in environment variables")
        print("\nPlease set your API key in one of these ways:")
        print("1. Create a .env file with: RAGFLOW_API_KEY=your-api-key-here")
        print("2. Set environment variable: export RAGFLOW_API_KEY=your-api-key-here")
        print("3. On Windows: set RAGFLOW_API_KEY=your-api-key-here")
        return

    # Get base URL from environment variable (optional, with default)
    BASE_URL = os.getenv("RAGFLOW_BASE_URL", "http://localhost:9380")

    print("=== RAGFlow Client Demo ===\n")
    print(f"📍 Connecting to: {BASE_URL}")

    # Initialize client
    client = RAGFlowClient(API_KEY, BASE_URL)

    # Test connection
    print("🔌 Testing connection to RAGFlow server...")
    if client.test_connection():
        print("✅ Connected successfully!")
    else:
        print("❌ Failed to connect to RAGFlow server")
        print("Make sure:")
        print("  1. RAGFlow server is running on localhost:9380")
        print("  2. Your API key is correct")
        print("  3. No firewall is blocking the connection")
        return

    # List existing datasets
    print("\n📚 Listing existing datasets...")
    datasets = client.list_datasets()
    if datasets is not None:
        if datasets:
            for dataset in datasets:
                print(f"  - {dataset.get('name', 'Unnamed')}: {dataset.get('description', 'No description')}")
        else:
            print("  No datasets found")

    # Example: Create a new dataset
    print("\n➕ Creating a new test dataset...")
    new_dataset = client.create_dataset("summer_dataset", "A test dataset created by Python client")
    if new_dataset:
        print(f"✅ Created dataset: {new_dataset.get('name')}")

    # List available chats and their IDs
    print("\n💬 Listing available chats...")
    chats = client.list_chats()
    if chats is not None:
        if chats:
            print("Available chat IDs:")
            for chat in chats:
                chat_id = chat.get('id', 'Unknown')
                chat_name = chat.get('name', 'Unnamed Chat')
                print(f"  - Chat ID: {chat_id}")
                print(f"    Name: {chat_name}")
                print(f"    Details: {chat}")
                print()
        else:
            print("  No chats found")

    # Example chat completion (using first available chat_id if any)
    print("\n🤖 Testing chat completion...")
    if chats and len(chats) > 0:
        first_chat_id = chats[0].get('id')
        if first_chat_id:
            print(f"Using chat ID: {first_chat_id}")
            chat_response = client.chat_completion(first_chat_id, "Hello, how are you?")
            if chat_response:
                print(f"Response: {chat_response}")
        else:
            print("No valid chat ID found in the first chat")
    else:
        print("No chats available to test with")


if __name__ == "__main__":
    main()