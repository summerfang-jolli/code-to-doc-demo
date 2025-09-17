#!/usr/bin/env python3
"""
Demo script showing how to use the Documentation Generator Agent.
This script generates documentation for the analyzed code elements.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.append('src')

from agents.doc_generator import DocumentationGeneratorAgent, DocStyle
from agents.code_analyzer import CodeAnalyzerAgent

# Import database utilities
sys.path.append('.')
from database.db_utils import get_code_element_manager

def main():
    """Demonstrate the Documentation Generator Agent."""
    print("📚 Documentation Generator Agent Demo")
    print("=" * 60)

    # Read the last project ID
    project_id_file = Path("last_project_id.txt")
    if not project_id_file.exists():
        print("❌ No project ID found. Run demo_analyzer.py first.")
        return 1

    project_id = project_id_file.read_text().strip()
    print(f"📁 Using project ID: {project_id}")

    # Get some elements to demonstrate with
    print("\n1. Getting code elements from database...")
    element_manager = get_code_element_manager()

    # Get code analyzer to find files for this project
    analyzer = CodeAnalyzerAgent()
    files = analyzer.file_manager.get_files_for_project(project_id)

    if not files:
        print("❌ No files found for this project")
        return 1

    # Get elements from the first file
    elements = element_manager.get_elements_for_file(files[0].id)

    if not elements:
        print("❌ No code elements found")
        return 1

    print(f"✅ Found {len(elements)} code elements in {files[0].file_path}")

    # Show available elements
    print("\n2. Available elements for documentation:")
    for i, element in enumerate(elements[:5]):  # Show first 5
        print(f"  {i+1}. {element.name} ({element.element_type}) - Complexity: {element.complexity_score}")

    # Initialize documentation generator
    print(f"\n3. Initializing Documentation Generator...")
    doc_generator = DocumentationGeneratorAgent(doc_style=DocStyle.GOOGLE)

    # Generate documentation for the first function or method
    target_element = None
    for element in elements:
        if element.element_type in ['function', 'method']:
            target_element = element
            break

    if not target_element:
        print("❌ No functions or methods found to document")
        return 1

    print(f"\n4. Generating documentation for: {target_element.name}")
    print(f"   Type: {target_element.element_type}")
    print(f"   Signature: {target_element.signature}")

    # Generate documentation
    result = doc_generator.generate_documentation_for_element(target_element.id)

    print(f"\n5. Documentation Generation Result:")
    print(f"Status: {result['status']}")

    if result['status'] == 'success':
        print(f"✅ Documentation generated successfully!")
        print(f"📊 Quality Scores:")
        scores = result['quality_scores']
        print(f"   Overall: {scores['overall_score']:.2f}")
        print(f"   Completeness: {scores['completeness_score']:.2f}")
        print(f"   Clarity: {scores['clarity_score']:.2f}")
        print(f"   Accuracy: {scores['accuracy_score']:.2f}")
        print(f"📝 Word Count: {result['word_count']}")
        print(f"💾 Documentation ID: {result['documentation_id']}")

        print(f"\n6. Generated Documentation:")
        print("=" * 60)
        print(result['documentation'])
        print("=" * 60)

        # Save the documentation ID for later use
        doc_id_file = Path("last_documentation_id.txt")
        doc_id_file.write_text(result['documentation_id'])
        print(f"\n💾 Documentation ID saved to: {doc_id_file}")

    else:
        print(f"❌ Documentation generation failed: {result['error']}")
        return 1

    print(f"\n7. What's Next?")
    print("You can now:")
    print("- Generate documentation for more elements")
    print("- Test different documentation styles (google, numpy, sphinx)")
    print("- Generate documentation for the entire project")
    print("- Create embeddings for semantic search")

    # Show database query to see the stored documentation
    print(f"\n8. View stored documentation in database:")
    print(f"   psql -d code_to_doc -c \"SELECT title, quality_score, word_count FROM documentation WHERE id = '{result['documentation_id']}';\"")

    return 0

def demo_project_documentation():
    """Demo generating documentation for an entire project."""
    print("\n" + "=" * 60)
    print("📚 Project Documentation Generation Demo")

    # Read the last project ID
    project_id_file = Path("last_project_id.txt")
    if not project_id_file.exists():
        print("❌ No project ID found. Run demo_analyzer.py first.")
        return

    project_id = project_id_file.read_text().strip()

    print(f"📁 Generating documentation for entire project: {project_id}")
    print("⚠️  This may take a while and use OpenAI API credits...")

    response = input("Continue? (y/N): ")
    if response.lower() != 'y':
        print("Cancelled.")
        return

    # Initialize documentation generator
    doc_generator = DocumentationGeneratorAgent(doc_style=DocStyle.GOOGLE)

    # Generate documentation for the entire project
    result = doc_generator.generate_documentation_for_project(project_id)

    print(f"\nProject Documentation Result:")
    if result['status'] == 'success':
        print(f"✅ Project documentation generated successfully!")
        print(f"📁 Files processed: {result['files_processed']}")
        print(f"🔧 Elements processed: {result['total_elements_processed']}")
        print(f"❌ Elements failed: {result['total_elements_failed']}")
        print(f"📚 Documentation items created: {len(result['documentation_ids'])}")

        if result['errors']:
            print(f"\n⚠️  Errors encountered:")
            for error in result['errors'][:3]:  # Show first 3 errors
                print(f"   - {error}")

    else:
        print(f"❌ Project documentation failed: {result['error']}")

def demo_different_styles():
    """Demo generating documentation in different styles."""
    print("\n" + "=" * 60)
    print("🎨 Documentation Style Comparison Demo")

    # Read the last project ID
    project_id_file = Path("last_project_id.txt")
    if not project_id_file.exists():
        print("❌ No project ID found. Run demo_analyzer.py first.")
        return

    project_id = project_id_file.read_text().strip()

    # Get an element to demonstrate with
    element_manager = get_code_element_manager()
    analyzer = CodeAnalyzerAgent()
    files = analyzer.file_manager.get_files_for_project(project_id)

    if not files:
        print("❌ No files found")
        return

    elements = element_manager.get_elements_for_file(files[0].id)
    target_element = None

    for element in elements:
        if element.element_type in ['function', 'method'] and element.complexity_score > 1.5:
            target_element = element
            break

    if not target_element:
        target_element = elements[0] if elements else None

    if not target_element:
        print("❌ No elements found")
        return

    print(f"📝 Generating documentation for: {target_element.name}")
    print(f"   Comparing different styles...")

    styles = [DocStyle.GOOGLE, DocStyle.NUMPY, DocStyle.API_REFERENCE]

    for style in styles:
        print(f"\n--- {style.value.upper()} STYLE ---")
        doc_generator = DocumentationGeneratorAgent(doc_style=style)
        result = doc_generator.generate_documentation_for_element(target_element.id)

        if result['status'] == 'success':
            print(f"✅ Generated (Quality: {result['quality_scores']['overall_score']:.2f})")
            print(result['documentation'][:200] + "...")
        else:
            print(f"❌ Failed: {result['error']}")

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Demo the Documentation Generator Agent')
    parser.add_argument('--project', action='store_true',
                       help='Demo project-wide documentation generation')
    parser.add_argument('--styles', action='store_true',
                       help='Demo different documentation styles')

    args = parser.parse_args()

    if args.project:
        demo_project_documentation()
    elif args.styles:
        demo_different_styles()
    else:
        exit_code = main()
        sys.exit(exit_code)