#!/usr/bin/env python3
"""
Demo script showing how to use the Code Analyzer Agent.
This script analyzes the sample project and shows the results.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.append('src')

from agents.code_analyzer import CodeAnalyzerAgent
import json

def main():
    """Demonstrate the Code Analyzer Agent."""
    print("🔍 Code Analyzer Agent Demo")
    print("=" * 50)

    # Initialize the agent
    print("1. Initializing Code Analyzer Agent...")
    agent = CodeAnalyzerAgent()

    # Analyze the sample project
    print("\n2. Analyzing sample project...")
    project_path = "examples/sample_project"

    result = agent.analyze_project(
        project_name="Sample FastAPI Project",
        directory_path=project_path,
        description="A sample FastAPI project for demonstrating code analysis and documentation generation"
    )

    # Display results
    print(f"\n3. Analysis Results:")
    print(f"Status: {result['status']}")

    if result['status'] == 'success':
        print(f"✅ Project created with ID: {result['project_id']}")
        print(f"📁 Files analyzed: {result['files_analyzed']}")
        print(f"❌ Files failed: {result['files_failed']}")
        print(f"🔧 Total elements found: {result['total_elements']}")

        print(f"\n4. Detailed File Results:")
        for file_result in result['file_results']:
            if file_result['status'] == 'success':
                print(f"  ✅ {file_result['file_path']}")
                print(f"     - Elements: {file_result['elements_found']}")
                print(f"     - Lines: {file_result['line_count']}")
                print(f"     - Size: {file_result['file_size']} bytes")
                if file_result['imports']:
                    print(f"     - Imports: {len(file_result['imports'])}")
            else:
                print(f"  ❌ {file_result['file_path']}: {file_result['error']}")

        # Get detailed summary
        print(f"\n5. Getting Analysis Summary...")
        summary = agent.get_analysis_summary(result['project_id'])

        if summary['status'] == 'success':
            print(f"\n📊 Project Summary:")
            print(f"Project: {summary['project_name']}")
            print(f"Total files: {summary['total_files']}")
            print(f"Total elements: {summary['total_elements']}")

            print(f"\n🏗️  Element Breakdown:")
            for element_type, count in summary['element_breakdown'].items():
                print(f"  {element_type}: {count}")

        # Store project ID for later use
        project_id_file = Path("last_project_id.txt")
        project_id_file.write_text(result['project_id'])
        print(f"\n💾 Project ID saved to: {project_id_file}")

    else:
        print(f"❌ Analysis failed: {result['error']}")
        return 1

    print(f"\n6. What's Next?")
    print("You can now:")
    print("- Run documentation generation on this project")
    print("- Query the database to see stored code elements")
    print("- Use the project ID for further analysis")

    # Show some database queries
    print(f"\n7. Sample Database Queries:")
    print("You can explore the results using psql:")
    print(f"  psql -d code_to_doc -c \"SELECT name, element_type FROM code_elements WHERE file_id IN (SELECT id FROM code_files WHERE project_id = '{result['project_id']}');\"")

    return 0

def demo_single_file():
    """Demo analyzing a single file."""
    print("\n" + "=" * 50)
    print("🔍 Single File Analysis Demo")

    # Read the last project ID
    project_id_file = Path("last_project_id.txt")
    if not project_id_file.exists():
        print("❌ No project ID found. Run main demo first.")
        return

    project_id = project_id_file.read_text().strip()

    agent = CodeAnalyzerAgent()

    # Analyze just the utils.py file
    result = agent.analyze_file("examples/sample_project/utils.py", project_id)

    print(f"Single file analysis result:")
    if result['status'] == 'success':
        print(f"✅ File: {result['file_path']}")
        print(f"🔧 Elements found: {result['elements_found']}")
        print(f"📏 Lines: {result['line_count']}")
        print(f"📦 Imports: {len(result.get('imports', []))}")
    else:
        print(f"❌ Error: {result['error']}")

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Demo the Code Analyzer Agent')
    parser.add_argument('--single-file', action='store_true',
                       help='Demo single file analysis')

    args = parser.parse_args()

    if args.single_file:
        demo_single_file()
    else:
        exit_code = main()
        sys.exit(exit_code)