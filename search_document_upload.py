"""
Search RAGFlow dataset for information about document uploading
"""

import argparse
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

from ragflow_client import RAGFlowClient

# Fix encoding for Windows console
if sys.platform == "win32":
    import codecs
    sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach())
    sys.stderr = codecs.getwriter("utf-8")(sys.stderr.detach())


def interactive_search():
    """Interactive search mode - continuously accept questions until user types quit()"""
    # Load environment variables
    load_dotenv()

    # Get API key from environment
    API_KEY = os.getenv("RAGFLOW_API_KEY")
    if not API_KEY:
        print("❌ Error: RAGFLOW_API_KEY not found in environment variables")
        print("Please set RAGFLOW_API_KEY in your .env file")
        return

    # Get base URL
    BASE_URL = os.getenv("RAGFLOW_BASE_URL", "http://localhost:9380")

    # Initialize client
    client = RAGFlowClient(API_KEY, BASE_URL)

    # Test connection
    print("🔌 Testing connection to RAGFlow server...")
    if not client.test_connection():
        print("❌ Failed to connect to RAGFlow server")
        print("Make sure RAGFlow is running on localhost:9380")
        return

    print("✅ Connected successfully!")

    # List available chats to find one connected to the "ragflow" dataset
    print("\n💬 Looking for available chats...")
    chats = client.list_chats()

    if not chats:
        print("❌ No chats found. Please create a chat in RAGFlow first.")
        return

    # Find a chat (preferably one connected to the ragflow dataset)
    target_chat = None

    # Look for a chat with "ragflow" in the name or use the first available
    for chat in chats:
        chat_name = chat.get('name', '').lower()
        if 'ragflow' in chat_name:
            target_chat = chat
            break

    # If no ragflow-specific chat found, use the first available
    if not target_chat and chats:
        target_chat = chats[0]

    if not target_chat:
        print("❌ No suitable chat found")
        return

    chat_id = target_chat.get('id')
    chat_name = target_chat.get('name', 'Unknown')

    print(f"📋 Using chat: {chat_name} (ID: {chat_id})")
    print("\n" + "=" * 60)
    print("🤖 Interactive RAGFlow Search")
    print("Type your questions and press Enter to search.")
    print("Type 'quit()' to exit.")
    print("=" * 60)

    # Interactive loop
    while True:
        try:
            # Get user input
            question = input("\n❓ Your question: ").strip()

            # Check if user wants to quit
            if question.lower() in ['quit()', 'quit', 'exit', 'q']:
                print("👋 Goodbye!")
                break

            # Skip empty questions
            if not question:
                print("Please enter a question or type 'quit()' to exit.")
                continue

            print("⏳ Searching for answer...")

            # Send the question to RAGFlow
            response = client.chat_completion(chat_id, question)

            if response:
                print(f"\n📖 Answer from RAGFlow:")
                print("-" * 60)
                print(response)
                print("-" * 60)
            else:
                print("❌ No response received or error occurred")
                print("This might happen if:")
                print("  - The chat is not connected to any dataset")
                print("  - The dataset doesn't contain relevant information")
                print("  - There's an issue with the RAGFlow API")

        except KeyboardInterrupt:
            print("\n\n👋 Interrupted by user. Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error occurred: {e}")
            print("Continuing... Type 'quit()' to exit.")


if __name__ == "__main__":
    interactive_search()
