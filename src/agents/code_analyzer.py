"""
Code Analyzer Agent - LangGraph agent for analyzing source code and storing results.
This agent uses AST parsing to extract code structure and stores it in PostgreSQL.
"""

import os
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import asdict

# Add src to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from tools.python_ast_parser import PythonASTParser, FileAnalysis, CodeElement
from config.settings import settings, get_db_config

# Import database utilities
sys.path.append(str(Path(__file__).parent.parent.parent))
from database.db_utils import (
    get_project_manager,
    get_code_file_manager,
    get_code_element_manager,
    ProjectManager,
    CodeFileManager,
    CodeElementManager
)

class CodeAnalyzerAgent:
    """
    LangGraph agent for analyzing source code files.

    This agent:
    1. Parses Python files using AST
    2. Extracts code elements (functions, classes, methods)
    3. Stores results in PostgreSQL database
    4. Tracks changes and updates
    """

    def __init__(self):
        self.parser = PythonASTParser()
        self.project_manager = get_project_manager()
        self.file_manager = get_code_file_manager()
        self.element_manager = get_code_element_manager()

    def analyze_file(self, file_path: str, project_id: str) -> Dict[str, Any]:
        """
        Analyze a single Python file and store results in database.

        Args:
            file_path: Path to the Python file to analyze
            project_id: ID of the project this file belongs to

        Returns:
            Dictionary with analysis results and statistics
        """
        try:
            # Parse the file
            analysis = self.parser.parse_file(file_path)

            # Store file in database
            file_id = self._store_file(analysis, project_id)

            # Store code elements
            element_ids = self._store_elements(analysis.elements, file_id)

            return {
                "status": "success",
                "file_path": file_path,
                "file_id": file_id,
                "elements_found": len(analysis.elements),
                "element_ids": element_ids,
                "file_size": analysis.file_size,
                "line_count": analysis.line_count,
                "imports": analysis.imports,
                "content_hash": analysis.content_hash
            }

        except Exception as e:
            return {
                "status": "error",
                "file_path": file_path,
                "error": str(e),
                "error_type": type(e).__name__
            }

    def analyze_directory(self, directory_path: str, project_id: str,
                         patterns: List[str] = None) -> Dict[str, Any]:
        """
        Analyze all Python files in a directory.

        Args:
            directory_path: Path to directory to analyze
            project_id: ID of the project
            patterns: File patterns to include (default: ['*.py'])

        Returns:
            Dictionary with analysis results for all files
        """
        if patterns is None:
            patterns = ['*.py']

        directory = Path(directory_path)
        if not directory.exists():
            return {
                "status": "error",
                "error": f"Directory not found: {directory_path}"
            }

        results = {
            "status": "success",
            "directory": str(directory),
            "files_analyzed": 0,
            "files_failed": 0,
            "total_elements": 0,
            "file_results": [],
            "errors": []
        }

        # Find all Python files
        python_files = []
        for pattern in patterns:
            python_files.extend(directory.rglob(pattern))

        # Analyze each file
        for file_path in python_files:
            try:
                result = self.analyze_file(str(file_path), project_id)

                if result["status"] == "success":
                    results["files_analyzed"] += 1
                    results["total_elements"] += result["elements_found"]
                else:
                    results["files_failed"] += 1
                    results["errors"].append(result)

                results["file_results"].append(result)

            except Exception as e:
                results["files_failed"] += 1
                results["errors"].append({
                    "file_path": str(file_path),
                    "error": str(e),
                    "error_type": type(e).__name__
                })

        return results

    def analyze_project(self, project_name: str, directory_path: str,
                       description: str = "", repository_url: str = "") -> Dict[str, Any]:
        """
        Analyze an entire project: create project record and analyze all files.

        Args:
            project_name: Name of the project
            directory_path: Root directory of the project
            description: Project description
            repository_url: Git repository URL

        Returns:
            Complete analysis results including project and file analysis
        """
        try:
            # Create project record
            project_id = self.project_manager.create_project(
                name=project_name,
                description=description,
                repository_url=repository_url,
                language="python",
                framework="",  # Could be detected from requirements.txt
                documentation_style="google"
            )

            # Analyze directory
            analysis_results = self.analyze_directory(directory_path, project_id)

            # Add project info to results
            analysis_results.update({
                "project_id": project_id,
                "project_name": project_name,
                "project_description": description
            })

            return analysis_results

        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "error_type": type(e).__name__
            }

    def get_analysis_summary(self, project_id: str) -> Dict[str, Any]:
        """Get a summary of analysis results for a project."""
        try:
            # Get project info
            project = self.project_manager.get_project(project_id)
            if not project:
                return {"status": "error", "error": "Project not found"}

            # Get files
            files = self.file_manager.get_files_for_project(project_id)

            # Get elements for each file
            total_elements = 0
            element_types = {}

            for file in files:
                elements = self.element_manager.get_elements_for_file(file.id)
                total_elements += len(elements)

                for element in elements:
                    element_types[element.element_type] = element_types.get(element.element_type, 0) + 1

            return {
                "status": "success",
                "project_name": project.name,
                "project_id": project_id,
                "total_files": len(files),
                "total_elements": total_elements,
                "element_breakdown": element_types,
                "files": [
                    {
                        "file_path": f.file_path,
                        "file_type": f.file_type,
                        "line_count": f.line_count,
                        "last_analyzed": f.last_analyzed.isoformat() if f.last_analyzed else None
                    }
                    for f in files
                ]
            }

        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "error_type": type(e).__name__
            }

    def _store_file(self, analysis: FileAnalysis, project_id: str) -> str:
        """Store file analysis in database."""
        # Determine file type from extension
        file_extension = Path(analysis.file_path).suffix.lower()
        file_type_map = {
            '.py': 'python',
            '.js': 'javascript',
            '.ts': 'typescript',
            '.java': 'java',
            '.cpp': 'cpp',
            '.c': 'c'
        }
        file_type = file_type_map.get(file_extension, 'unknown')

        return self.file_manager.add_file(
            project_id=project_id,
            file_path=analysis.file_path,
            content=analysis.content,
            file_type=file_type
        )

    def _store_elements(self, elements: List[CodeElement], file_id: str) -> List[str]:
        """Store code elements in database."""
        element_ids = []

        for element in elements:
            element_id = self.element_manager.add_element(
                file_id=file_id,
                element_type=element.element_type,
                name=element.name,
                full_name=element.full_name,
                signature=element.signature,
                docstring=element.docstring,
                start_line=element.start_line,
                end_line=element.end_line,
                complexity_score=element.complexity_score,
                dependencies=element.dependencies,
                parameters=element.parameters,
                return_type=element.return_type,
                visibility=element.visibility
            )
            element_ids.append(element_id)

        return element_ids

# Convenience functions for direct usage
def analyze_single_file(file_path: str, project_id: str) -> Dict[str, Any]:
    """Analyze a single file - convenience function."""
    agent = CodeAnalyzerAgent()
    return agent.analyze_file(file_path, project_id)

def analyze_project_directory(project_name: str, directory_path: str) -> Dict[str, Any]:
    """Analyze an entire project directory - convenience function."""
    agent = CodeAnalyzerAgent()
    return agent.analyze_project(project_name, directory_path)

# CLI interface for testing
def main():
    """Command-line interface for the Code Analyzer Agent."""
    import argparse

    parser = argparse.ArgumentParser(description='Analyze Python code and store in database')
    parser.add_argument('command', choices=['file', 'project', 'summary'],
                       help='Command to execute')
    parser.add_argument('--file', '-f', help='Python file to analyze')
    parser.add_argument('--project', '-p', help='Project name')
    parser.add_argument('--directory', '-d', help='Directory to analyze')
    parser.add_argument('--project-id', help='Existing project ID')
    parser.add_argument('--description', help='Project description')

    args = parser.parse_args()

    agent = CodeAnalyzerAgent()

    if args.command == 'file':
        if not args.file or not args.project_id:
            print("Error: --file and --project-id required for file analysis")
            return

        result = agent.analyze_file(args.file, args.project_id)
        print("File Analysis Result:")
        print(f"Status: {result['status']}")
        if result['status'] == 'success':
            print(f"Elements found: {result['elements_found']}")
            print(f"File size: {result['file_size']} bytes")
            print(f"Lines: {result['line_count']}")
        else:
            print(f"Error: {result['error']}")

    elif args.command == 'project':
        if not args.project or not args.directory:
            print("Error: --project and --directory required for project analysis")
            return

        result = agent.analyze_project(
            project_name=args.project,
            directory_path=args.directory,
            description=args.description or ""
        )
        print("Project Analysis Result:")
        print(f"Status: {result['status']}")
        if result['status'] == 'success':
            print(f"Project ID: {result['project_id']}")
            print(f"Files analyzed: {result['files_analyzed']}")
            print(f"Total elements: {result['total_elements']}")
            if result['files_failed'] > 0:
                print(f"Files failed: {result['files_failed']}")
        else:
            print(f"Error: {result['error']}")

    elif args.command == 'summary':
        if not args.project_id:
            print("Error: --project-id required for summary")
            return

        result = agent.get_analysis_summary(args.project_id)
        print("Analysis Summary:")
        print(f"Status: {result['status']}")
        if result['status'] == 'success':
            print(f"Project: {result['project_name']}")
            print(f"Total files: {result['total_files']}")
            print(f"Total elements: {result['total_elements']}")
            print("Element breakdown:")
            for element_type, count in result['element_breakdown'].items():
                print(f"  {element_type}: {count}")
        else:
            print(f"Error: {result['error']}")

if __name__ == "__main__":
    main()