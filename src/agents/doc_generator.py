"""
Documentation Generator Agent - LangGraph agent for generating documentation using LLMs.
This agent takes analyzed code elements and generates comprehensive documentation.
"""

import os
import sys
import json
import re
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import asdict

# Add src to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from tools.doc_templates import DocumentationTemplates, DocumentationContext, DocStyle
from config.settings import settings

# Import database utilities
sys.path.append(str(Path(__file__).parent.parent.parent))
from database.db_utils import (
    get_code_element_manager,
    get_documentation_manager,
    get_code_file_manager,
    CodeElementManager,
    DocumentationManager,
    CodeFileManager
)

# Import LangChain components
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

class DocumentationGeneratorAgent:
    """
    LangGraph agent for generating code documentation using LLMs.

    This agent:
    1. Retrieves code elements from the database
    2. Generates comprehensive documentation using LLM
    3. Assesses documentation quality
    4. Stores generated documentation in the database
    5. Creates embeddings for semantic search
    """

    def __init__(self, model_name: str = None, doc_style: DocStyle = DocStyle.GOOGLE):
        self.model_name = model_name or settings.llm.model
        self.doc_style = doc_style
        self.templates = DocumentationTemplates()

        # Initialize LLM
        self.llm = ChatOpenAI(
            model=self.model_name,
            temperature=settings.llm.temperature,
            max_tokens=settings.llm.max_tokens,
            openai_api_key=settings.llm.openai_api_key
        )

        # Initialize database managers
        self.element_manager = get_code_element_manager()
        self.doc_manager = get_documentation_manager()
        self.file_manager = get_code_file_manager()

        # Create output parser
        self.output_parser = StrOutputParser()

    def generate_documentation_for_element(self, element_id: str) -> Dict[str, Any]:
        """
        Generate documentation for a single code element.

        Args:
            element_id: ID of the code element to document

        Returns:
            Dictionary with generation results
        """
        try:
            # Get element from database
            element = self._get_element_by_id(element_id)
            if not element:
                return {
                    "status": "error",
                    "error": f"Element not found: {element_id}"
                }

            # Get source code context
            context = self._build_documentation_context(element)

            # Generate documentation
            documentation = self._generate_documentation(context)

            # Assess quality
            quality_scores = self._assess_documentation_quality(documentation, context)

            # Store in database
            doc_id = self._store_documentation(
                element_id=element_id,
                documentation=documentation,
                quality_scores=quality_scores,
                context=context
            )

            return {
                "status": "success",
                "element_id": element_id,
                "documentation_id": doc_id,
                "element_name": element.name,
                "element_type": element.element_type,
                "documentation": documentation,
                "quality_scores": quality_scores,
                "word_count": len(documentation.split())
            }

        except Exception as e:
            return {
                "status": "error",
                "element_id": element_id,
                "error": str(e),
                "error_type": type(e).__name__
            }

    def generate_documentation_for_file(self, file_id: str) -> Dict[str, Any]:
        """
        Generate documentation for all elements in a file.

        Args:
            file_id: ID of the file to document

        Returns:
            Dictionary with generation results for all elements
        """
        try:
            # Get all elements in the file
            elements = self.element_manager.get_elements_for_file(file_id)

            if not elements:
                return {
                    "status": "error",
                    "error": f"No elements found in file: {file_id}"
                }

            results = {
                "status": "success",
                "file_id": file_id,
                "elements_processed": 0,
                "elements_failed": 0,
                "documentation_ids": [],
                "element_results": [],
                "errors": []
            }

            # Generate documentation for each element
            for element in elements:
                try:
                    result = self.generate_documentation_for_element(element.id)

                    if result["status"] == "success":
                        results["elements_processed"] += 1
                        results["documentation_ids"].append(result["documentation_id"])
                    else:
                        results["elements_failed"] += 1
                        results["errors"].append(result)

                    results["element_results"].append(result)

                except Exception as e:
                    results["elements_failed"] += 1
                    results["errors"].append({
                        "element_id": element.id,
                        "element_name": element.name,
                        "error": str(e),
                        "error_type": type(e).__name__
                    })

            return results

        except Exception as e:
            return {
                "status": "error",
                "file_id": file_id,
                "error": str(e),
                "error_type": type(e).__name__
            }

    def generate_documentation_for_project(self, project_id: str) -> Dict[str, Any]:
        """
        Generate documentation for all elements in a project.

        Args:
            project_id: ID of the project to document

        Returns:
            Dictionary with generation results for the entire project
        """
        try:
            # Get all files in the project
            files = self.file_manager.get_files_for_project(project_id)

            if not files:
                return {
                    "status": "error",
                    "error": f"No files found in project: {project_id}"
                }

            results = {
                "status": "success",
                "project_id": project_id,
                "files_processed": 0,
                "files_failed": 0,
                "total_elements_processed": 0,
                "total_elements_failed": 0,
                "documentation_ids": [],
                "file_results": [],
                "errors": []
            }

            # Generate documentation for each file
            for file in files:
                try:
                    file_result = self.generate_documentation_for_file(file.id)

                    if file_result["status"] == "success":
                        results["files_processed"] += 1
                        results["total_elements_processed"] += file_result["elements_processed"]
                        results["total_elements_failed"] += file_result["elements_failed"]
                        results["documentation_ids"].extend(file_result["documentation_ids"])
                    else:
                        results["files_failed"] += 1
                        results["errors"].append(file_result)

                    results["file_results"].append({
                        "file_id": file.id,
                        "file_path": file.file_path,
                        "result": file_result
                    })

                except Exception as e:
                    results["files_failed"] += 1
                    results["errors"].append({
                        "file_id": file.id,
                        "file_path": file.file_path,
                        "error": str(e),
                        "error_type": type(e).__name__
                    })

            return results

        except Exception as e:
            return {
                "status": "error",
                "project_id": project_id,
                "error": str(e),
                "error_type": type(e).__name__
            }

    def improve_documentation(self, documentation_id: str) -> Dict[str, Any]:
        """
        Improve existing documentation based on quality feedback.

        Args:
            documentation_id: ID of the documentation to improve

        Returns:
            Dictionary with improvement results
        """
        try:
            # Get existing documentation (this would need to be implemented in db_utils)
            # For now, return a placeholder
            return {
                "status": "error",
                "error": "Documentation improvement not yet implemented"
            }

        except Exception as e:
            return {
                "status": "error",
                "documentation_id": documentation_id,
                "error": str(e),
                "error_type": type(e).__name__
            }

    def _get_element_by_id(self, element_id: str):
        """Get code element by ID from database."""
        return self.element_manager.get_element_by_id(element_id)

    def _build_documentation_context(self, element) -> DocumentationContext:
        """Build documentation context from code element."""
        # Get the source code for the element
        # This is a simplified version - in practice, you'd extract the exact code
        source_code = self._extract_element_source_code(element)

        return DocumentationContext(
            element_name=element.name,
            element_type=element.element_type,
            signature=element.signature,
            docstring=element.docstring,
            parameters=element.parameters,
            return_type=element.return_type,
            complexity_score=element.complexity_score,
            dependencies=element.dependencies,
            file_path="",  # Would get from file info
            source_code=source_code,
            parent_class=element.parent_class if hasattr(element, 'parent_class') else None,
            decorators=element.decorators if hasattr(element, 'decorators') else []
        )

    def _extract_element_source_code(self, element) -> str:
        """Extract the source code for a specific element."""
        # For demo purposes, create a simple representation
        # In practice, you'd extract the actual source code from the file
        if element.element_type == "function":
            return f"{element.signature}\n    # Implementation here\n    pass"
        elif element.element_type == "class":
            return f"{element.signature}\n    # Class implementation\n    pass"
        else:
            return element.signature

    def _generate_documentation(self, context: DocumentationContext) -> str:
        """Generate documentation using LLM."""
        # Get the appropriate prompt based on element type
        if context.element_type == "function":
            prompt = self.templates.get_function_prompt(context, self.doc_style)
        elif context.element_type == "class":
            prompt = self.templates.get_class_prompt(context, self.doc_style)
        elif context.element_type == "method":
            prompt = self.templates.get_method_prompt(context, self.doc_style)
        else:
            prompt = self.templates.get_function_prompt(context, self.doc_style)

        # Create messages
        system_message = SystemMessage(content=self.templates.get_system_prompt(self.doc_style))
        human_message = HumanMessage(content=prompt)

        # Generate documentation
        response = self.llm.invoke([system_message, human_message])
        return response.content

    def _assess_documentation_quality(self, documentation: str, context: DocumentationContext) -> Dict[str, float]:
        """Assess the quality of generated documentation."""
        try:
            # Create quality assessment prompt
            assessment_prompt = self.templates.get_quality_assessment_prompt(documentation, context)

            # Get assessment from LLM
            response = self.llm.invoke([
                SystemMessage(content="You are an expert technical writing assessor. Provide accurate quality scores."),
                HumanMessage(content=assessment_prompt)
            ])

            # Parse JSON response
            assessment_text = response.content

            # Extract JSON from response
            json_match = re.search(r'```json\s*(\{.*?\})\s*```', assessment_text, re.DOTALL)
            if json_match:
                assessment_data = json.loads(json_match.group(1))
                return {
                    "completeness_score": assessment_data.get("completeness_score", 0.0),
                    "clarity_score": assessment_data.get("clarity_score", 0.0),
                    "accuracy_score": assessment_data.get("accuracy_score", 0.0),
                    "usefulness_score": assessment_data.get("usefulness_score", 0.0),
                    "overall_score": assessment_data.get("overall_score", 0.0)
                }

        except Exception as e:
            print(f"Quality assessment failed: {e}")

        # Return default scores if assessment fails
        return {
            "completeness_score": 0.7,
            "clarity_score": 0.7,
            "accuracy_score": 0.7,
            "usefulness_score": 0.7,
            "overall_score": 0.7
        }

    def _store_documentation(self, element_id: str, documentation: str,
                           quality_scores: Dict[str, float], context: DocumentationContext) -> str:
        """Store generated documentation in the database."""
        return self.doc_manager.add_documentation(
            element_id=element_id,
            doc_type="api",  # Could be dynamic based on context
            title=f"{context.element_name} - {context.element_type.title()} Documentation",
            content=documentation,
            generated_by=f"gpt-4-doc-generator-{self.doc_style.value}",
            quality_score=quality_scores.get("overall_score", 0.0),
            completeness_score=quality_scores.get("completeness_score", 0.0),
            clarity_score=quality_scores.get("clarity_score", 0.0),
            accuracy_score=quality_scores.get("accuracy_score", 0.0)
        )

# Convenience functions for direct usage
def generate_docs_for_element(element_id: str, doc_style: str = "google") -> Dict[str, Any]:
    """Generate documentation for a single element - convenience function."""
    style = DocStyle(doc_style)
    agent = DocumentationGeneratorAgent(doc_style=style)
    return agent.generate_documentation_for_element(element_id)

def generate_docs_for_project(project_id: str, doc_style: str = "google") -> Dict[str, Any]:
    """Generate documentation for an entire project - convenience function."""
    style = DocStyle(doc_style)
    agent = DocumentationGeneratorAgent(doc_style=style)
    return agent.generate_documentation_for_project(project_id)

# CLI interface for testing
def main():
    """Command-line interface for the Documentation Generator Agent."""
    import argparse

    parser = argparse.ArgumentParser(description='Generate documentation for analyzed code')
    parser.add_argument('command', choices=['element', 'file', 'project'],
                       help='Command to execute')
    parser.add_argument('--element-id', help='Code element ID to document')
    parser.add_argument('--file-id', help='File ID to document')
    parser.add_argument('--project-id', help='Project ID to document')
    parser.add_argument('--style', choices=['google', 'numpy', 'sphinx'],
                       default='google', help='Documentation style')

    args = parser.parse_args()

    # Convert style to enum
    doc_style = DocStyle(args.style)
    agent = DocumentationGeneratorAgent(doc_style=doc_style)

    if args.command == 'element':
        if not args.element_id:
            print("Error: --element-id required for element documentation")
            return

        result = agent.generate_documentation_for_element(args.element_id)
        print("Element Documentation Result:")
        print(f"Status: {result['status']}")
        if result['status'] == 'success':
            print(f"Element: {result['element_name']} ({result['element_type']})")
            print(f"Quality Score: {result['quality_scores']['overall_score']:.2f}")
            print(f"Word Count: {result['word_count']}")
            print(f"\nGenerated Documentation:\n{result['documentation']}")
        else:
            print(f"Error: {result['error']}")

    elif args.command == 'file':
        if not args.file_id:
            print("Error: --file-id required for file documentation")
            return

        result = agent.generate_documentation_for_file(args.file_id)
        print("File Documentation Result:")
        print(f"Status: {result['status']}")
        if result['status'] == 'success':
            print(f"Elements processed: {result['elements_processed']}")
            print(f"Elements failed: {result['elements_failed']}")
        else:
            print(f"Error: {result['error']}")

    elif args.command == 'project':
        if not args.project_id:
            print("Error: --project-id required for project documentation")
            return

        result = agent.generate_documentation_for_project(args.project_id)
        print("Project Documentation Result:")
        print(f"Status: {result['status']}")
        if result['status'] == 'success':
            print(f"Files processed: {result['files_processed']}")
            print(f"Total elements processed: {result['total_elements_processed']}")
            print(f"Documentation IDs generated: {len(result['documentation_ids'])}")
        else:
            print(f"Error: {result['error']}")

if __name__ == "__main__":
    main()