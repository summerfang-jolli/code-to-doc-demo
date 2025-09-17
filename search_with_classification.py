"""
Search RAGFlow dataset with LangGraph classification enhancement
"""

import os
import sys
from typing import TypedDict, List

from dotenv import load_dotenv
from langgraph.graph import StateGraph, END
from langchain_core.messages import AIMessage
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

from ragflow_client import RAGFlowClient

# Fix encoding for Windows console
if sys.platform == "win32":
    import codecs
    sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach())
    sys.stderr = codecs.getwriter("utf-8")(sys.stderr.detach())


# State definition for LangGraph
class ClassificationState(TypedDict):
    original_question: str
    refined_question: str
    question_type: str
    messages: List[str]


def classify_question(state: ClassificationState) -> ClassificationState:
    """Classify the user's question to determine the type"""
    llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0)

    classification_prompt = ChatPromptTemplate.from_template("""
    Analyze the following question and classify it into one of these categories:
    - "python_installation": Questions about installing Python packages, dependencies, or setup
    - "general": All other questions

    Question: {question}

    Respond with only the category name (python_installation or general).
    """)

    response = llm.invoke(classification_prompt.format(question=state["original_question"]))
    state["question_type"] = response.content.strip().lower()
    state["messages"].append(f"Classified as: {state['question_type']}")

    return state


def refine_installation_question(state: ClassificationState) -> ClassificationState:
    """Refine Python installation questions to the specified format"""
    if state["question_type"] == "python_installation":
        llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0)

        refinement_prompt = ChatPromptTemplate.from_template("""
        The user asked a Python installation question. Extract the package name from their question
        and reformat it to: "Give me just the prerequisites and pip install command for [package_name], nothing else. Do not include how does it come back what knowledge you have about the package in the response."

        Original question: {question}

        If you can identify a specific package name, use the format above.
        If no specific package is mentioned, ask them to specify the package name.
        """)

        response = llm.invoke(refinement_prompt.format(question=state["original_question"]))
        state["refined_question"] = response.content.strip()
        state["messages"].append(f"Refined question: {state['refined_question']}")
    else:
        # For non-installation questions, use the original question
        state["refined_question"] = state["original_question"]
        state["messages"].append("Using original question (no refinement needed)")

    return state


def build_classification_graph():
    """Build the LangGraph workflow for question classification"""
    workflow = StateGraph(ClassificationState)

    # Add nodes
    workflow.add_node("classify", classify_question)
    workflow.add_node("refine", refine_installation_question)

    # Add edges
    workflow.set_entry_point("classify")
    workflow.add_edge("classify", "refine")
    workflow.add_edge("refine", END)

    return workflow.compile()


def interactive_search():
    """Interactive search mode with LangGraph classification"""
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

    # Build the classification graph
    print("🧠 Initializing LangGraph classification system...")
    classification_graph = build_classification_graph()

    print("\n" + "=" * 60)
    print("🤖 Interactive RAGFlow Search with LangGraph Classification")
    print("Type your questions and press Enter to search.")
    print("Python installation questions will be automatically refined.")
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

            print("🔍 Classifying and refining your question...")

            # Create initial state
            state = {
                "original_question": question,
                "refined_question": "",
                "question_type": "",
                "messages": []
            }

            # Run the classification workflow
            result = classification_graph.invoke(state)

            # Show classification results
            print(f"📊 Question type: {result['question_type']}")
            if result["question_type"] == "python_installation":
                print(f"✏️  Refined question: {result['refined_question']}")
                final_question = result["refined_question"]
            else:
                print("📝 Using original question")
                final_question = result["original_question"]

            print("⏳ Searching for answer...")

            # Send the refined question to RAGFlow
            response = client.chat_completion(chat_id, final_question)

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