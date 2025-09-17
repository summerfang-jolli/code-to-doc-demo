#!/usr/bin/env python3
"""
Test script to verify the setup is working correctly.
This should be run before starting the main development.
"""

import os
import sys
sys.path.append('src')

def test_environment():
    """Test environment variables."""
    print("🔍 Testing environment setup...")

    try:
        from src.config.settings import settings

        # Test if settings can load properly
        db_url = settings.database.connection_url
        api_key = settings.llm.openai_api_key

        print(f"✅ DATABASE_URL: postgresql://.../{settings.database.name}")
        print(f"✅ OPENAI_API_KEY: {'*' * 10}{api_key[-4:]}")
        print("✅ Environment variables OK")
        return True

    except Exception as e:
        print(f"❌ Environment configuration failed: {e}")
        return False

def test_database_connection():
    """Test database connectivity."""
    print("\n🔍 Testing database connection...")

    try:
        import psycopg2
        from src.config.settings import get_db_config

        config = get_db_config()
        conn = psycopg2.connect(**config)
        cursor = conn.cursor()

        # Test basic query
        cursor.execute("SELECT COUNT(*) FROM projects")
        count = cursor.fetchone()[0]
        print(f"✅ Database connected: {count} projects found")

        # Test vector extension
        cursor.execute("SELECT COUNT(*) FROM document_embeddings")
        embedding_count = cursor.fetchone()[0]
        print(f"✅ Vector store connected: {embedding_count} embeddings found")

        cursor.close()
        conn.close()
        return True

    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        return False
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

def test_dependencies():
    """Test required Python dependencies."""
    print("\n🔍 Testing Python dependencies...")

    required_packages = [
        'psycopg2',
        'pydantic',
        'dotenv',
        'openai',
        'langchain',
        'langgraph'
    ]

    missing_packages = []

    for package in required_packages:
        try:
            __import__(package)
            print(f"✅ {package}")
        except ImportError:
            missing_packages.append(package)
            print(f"❌ {package}")

    if missing_packages:
        print(f"\n💡 Install missing packages with:")
        print(f"pip install {' '.join(missing_packages)}")
        return False

    print("✅ All dependencies OK")
    return True

def test_directory_structure():
    """Test project directory structure."""
    print("\n🔍 Testing directory structure...")

    required_dirs = [
        'src',
        'src/agents',
        'src/workflow',
        'src/tools',
        'src/config',
        'database',
        'tests',
        'examples'
    ]

    missing_dirs = []

    for dir_path in required_dirs:
        if os.path.exists(dir_path):
            print(f"✅ {dir_path}/")
        else:
            missing_dirs.append(dir_path)
            print(f"❌ {dir_path}/")

    if missing_dirs:
        print(f"💡 Create missing directories:")
        for dir_path in missing_dirs:
            print(f"mkdir -p {dir_path}")
        return False

    print("✅ Directory structure OK")
    return True

def main():
    """Run all tests."""
    print("🚀 Code-to-Documentation Setup Test")
    print("=" * 40)

    tests = [
        test_directory_structure,
        test_environment,
        test_dependencies,
        test_database_connection
    ]

    all_passed = True

    for test in tests:
        try:
            if not test():
                all_passed = False
        except Exception as e:
            print(f"❌ Test failed with error: {e}")
            all_passed = False

    print("\n" + "=" * 40)
    if all_passed:
        print("🎉 All tests passed! Ready to start development.")
        print("\nNext steps:")
        print("1. Install dependencies: pip install -r requirements.txt")
        print("2. Start building agents: python src/agents/code_analyzer.py")
    else:
        print("⚠️  Some tests failed. Please fix the issues above.")
        return 1

    return 0

if __name__ == "__main__":
    exit(main())