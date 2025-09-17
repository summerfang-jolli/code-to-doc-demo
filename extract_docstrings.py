#!/usr/bin/env python3
"""
Extract function signatures and docstrings from source code for RAGFlow storage.
Creates structured data suitable for RAG-based code documentation search.
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Any
from dataclasses import asdict

# Add src to path
sys.path.append('src')
from tools.python_ast_parser import PythonASTParser, CodeElement

class DocstringExtractor:
    """Extract function signatures and docstrings for RAGFlow storage."""

    def __init__(self):
        self.parser = PythonASTParser()

    def extract_from_file(self, file_path: str) -> Dict[str, Any]:
        """Extract docstrings from a single Python file."""
        try:
            analysis = self.parser.parse_file(file_path)
            return self._process_elements(analysis.elements, file_path)
        except Exception as e:
            print(f"Error processing {file_path}: {e}")
            return {}

    def extract_from_directory(self, directory: str, pattern: str = "**/*.py") -> Dict[str, Any]:
        """Extract docstrings from all Python files in a directory."""
        path = Path(directory)
        all_functions = {}

        for file_path in path.glob(pattern):
            if file_path.is_file():
                file_functions = self.extract_from_file(str(file_path))
                all_functions.update(file_functions)

        return all_functions

    def _process_elements(self, elements: List[CodeElement], file_path: str) -> Dict[str, Any]:
        """Process code elements and extract function info."""
        functions = {}

        for element in elements:
            if element.element_type in ['function', 'method'] and element.docstring.strip():
                # Create unique key: filename:function_name:signature_hash
                key = self._create_function_key(element, file_path)

                # Create function info for RAGFlow
                function_info = {
                    'signature': element.signature,
                    'docstring': element.docstring.strip(),
                    'metadata': {
                        'file_path': file_path,
                        'function_name': element.name,
                        'full_name': element.full_name,
                        'element_type': element.element_type,
                        'start_line': element.start_line,
                        'end_line': element.end_line,
                        'complexity_score': element.complexity_score,
                        'visibility': element.visibility,
                        'is_async': element.is_async,
                        'is_static': element.is_static,
                        'parameters': element.parameters,
                        'return_type': element.return_type,
                        'decorators': element.decorators,
                        'parent_class': element.parent_class
                    }
                }

                functions[key] = function_info

        return functions

    def _create_function_key(self, element: CodeElement, file_path: str) -> str:
        """Create a unique key for the function."""
        # Use relative path for cleaner keys
        rel_path = Path(file_path).name

        # Include class name if it's a method
        if element.parent_class:
            return f"{rel_path}:{element.parent_class}.{element.name}"
        else:
            return f"{rel_path}:{element.name}"

    def save_to_json(self, functions: Dict[str, Any], output_file: str) -> None:
        """Save extracted functions to JSON file."""
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(functions, f, indent=2, ensure_ascii=False)
        print(f"✅ Saved {len(functions)} functions to {output_file}")

    def create_ragflow_documents(self, functions: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Create documents suitable for RAGFlow ingestion."""
        documents = []

        for key, func_info in functions.items():
            # Create a comprehensive document for each function
            document = {
                'id': key,
                'title': f"{func_info['metadata']['function_name']} - {func_info['metadata']['file_path']}",
                'content': self._create_document_content(func_info),
                'metadata': func_info['metadata']
            }
            documents.append(document)

        return documents

    def _create_document_content(self, func_info: Dict[str, Any]) -> str:
        """Create comprehensive content for RAGFlow document."""
        metadata = func_info['metadata']

        content_parts = [
            f"Function: {metadata['function_name']}",
            f"Signature: {func_info['signature']}",
            f"File: {metadata['file_path']}",
            f"Type: {metadata['element_type']}",
        ]

        if metadata['parent_class']:
            content_parts.append(f"Class: {metadata['parent_class']}")

        if metadata['parameters']:
            params = [f"{p['name']}: {p['type']}" for p in metadata['parameters']]
            content_parts.append(f"Parameters: {', '.join(params)}")

        content_parts.extend([
            f"Returns: {metadata['return_type']}",
            f"Complexity: {metadata['complexity_score']}",
            "",
            "Documentation:",
            func_info['docstring']
        ])

        return "\n".join(content_parts)

def main():
    """Main function to demonstrate the extractor."""
    import argparse

    parser = argparse.ArgumentParser(description='Extract function docstrings for RAGFlow')
    parser.add_argument('--input', '-i', required=True,
                       help='Input file or directory to process')
    parser.add_argument('--output', '-o', default='function_docstrings.json',
                       help='Output JSON file (default: function_docstrings.json)')
    parser.add_argument('--ragflow', '-r', action='store_true',
                       help='Generate RAGFlow-ready documents')
    parser.add_argument('--ragflow-output', default='ragflow_documents.json',
                       help='RAGFlow documents output file')

    args = parser.parse_args()

    extractor = DocstringExtractor()

    print("🔍 Extracting function docstrings...")

    # Extract functions
    input_path = Path(args.input)
    if input_path.is_file():
        functions = extractor.extract_from_file(args.input)
    else:
        functions = extractor.extract_from_directory(args.input)

    if not functions:
        print("❌ No functions with docstrings found")
        return 1

    print(f"✅ Found {len(functions)} functions with docstrings")

    # Save to JSON
    extractor.save_to_json(functions, args.output)

    # Generate RAGFlow documents if requested
    if args.ragflow:
        print("\n📚 Creating RAGFlow documents...")
        documents = extractor.create_ragflow_documents(functions)

        with open(args.ragflow_output, 'w', encoding='utf-8') as f:
            json.dump(documents, f, indent=2, ensure_ascii=False)

        print(f"✅ Created {len(documents)} RAGFlow documents in {args.ragflow_output}")

        # Show sample document
        if documents:
            print(f"\n📄 Sample document:")
            print("-" * 50)
            print(f"ID: {documents[0]['id']}")
            print(f"Title: {documents[0]['title']}")
            print(f"Content preview: {documents[0]['content'][:200]}...")

    return 0

if __name__ == "__main__":
    sys.exit(main())