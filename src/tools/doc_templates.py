"""
Documentation templates and prompts for generating high-quality code documentation.
Contains templates for different documentation styles and code element types.
"""

from typing import Dict, Any, List
from dataclasses import dataclass
from enum import Enum

class DocStyle(Enum):
    """Documentation styles supported."""
    GOOGLE = "google"
    NUMPY = "numpy"
    SPHINX = "sphinx"
    API_REFERENCE = "api_reference"
    TUTORIAL = "tutorial"

class ElementType(Enum):
    """Code element types."""
    FUNCTION = "function"
    METHOD = "method"
    CLASS = "class"
    MODULE = "module"
    VARIABLE = "variable"

@dataclass
class DocumentationContext:
    """Context information for documentation generation."""
    element_name: str
    element_type: str
    signature: str
    docstring: str
    parameters: List[Dict[str, Any]]
    return_type: str
    complexity_score: float
    dependencies: List[str]
    file_path: str
    source_code: str
    parent_class: str = None
    decorators: List[str] = None

class DocumentationTemplates:
    """Templates for generating documentation using LLMs."""

    @staticmethod
    def get_system_prompt(doc_style: DocStyle = DocStyle.GOOGLE) -> str:
        """Get the system prompt for the documentation generation LLM."""

        base_prompt = """You are an expert technical writer specializing in Python code documentation.
Your task is to generate comprehensive, accurate, and helpful documentation for code elements.

Key principles:
1. Be accurate and factual - never make assumptions about functionality not evident in the code
2. Be comprehensive - cover all important aspects of the code element
3. Be clear and accessible - write for developers who will use this code
4. Follow the specified documentation style consistently
5. Include practical examples when helpful
6. Explain complex concepts in simple terms
7. Highlight important warnings or edge cases

"""

        style_guidance = {
            DocStyle.GOOGLE: """
Follow Google docstring style:
- Use clear, concise descriptions
- Document Args, Returns, Raises sections consistently
- Use proper formatting with sections and indentation
""",
            DocStyle.NUMPY: """
Follow NumPy docstring style:
- Use longer form descriptions with parameters and returns sections
- Include detailed type information
- Use proper NumPy formatting conventions
""",
            DocStyle.API_REFERENCE: """
Generate API reference documentation:
- Focus on technical details and usage patterns
- Include code examples for complex functions
- Document all parameters and return values thoroughly
- Include error conditions and edge cases
""",
            DocStyle.TUTORIAL: """
Generate tutorial-style documentation:
- Explain not just what the code does, but why and how to use it
- Include step-by-step examples
- Provide context and background information
- Focus on practical usage scenarios
"""
        }

        return base_prompt + style_guidance.get(doc_style, style_guidance[DocStyle.GOOGLE])

    @staticmethod
    def get_function_prompt(context: DocumentationContext, doc_style: DocStyle = DocStyle.GOOGLE) -> str:
        """Generate prompt for documenting a function."""

        prompt = f"""Generate comprehensive documentation for the following Python function:

**Function Information:**
- Name: {context.element_name}
- Signature: {context.signature}
- File: {context.file_path}
- Complexity Score: {context.complexity_score}

**Source Code:**
```python
{context.source_code}
```

**Existing Docstring:**
{context.docstring if context.docstring else "None"}

**Parameters:**
{DocumentationTemplates._format_parameters(context.parameters)}

**Return Type:** {context.return_type}

**Dependencies:** {', '.join(context.dependencies) if context.dependencies else 'None'}

**Decorators:** {', '.join(context.decorators) if context.decorators else 'None'}

Please generate documentation that includes:
1. A clear, comprehensive description of what the function does
2. Detailed parameter documentation with types and descriptions
3. Return value documentation
4. Any exceptions that might be raised
5. Usage examples if the function is complex
6. Performance considerations if relevant
7. Important notes or warnings

Format the documentation as a complete docstring in {doc_style.value} style.
"""
        return prompt

    @staticmethod
    def get_class_prompt(context: DocumentationContext, doc_style: DocStyle = DocStyle.GOOGLE) -> str:
        """Generate prompt for documenting a class."""

        prompt = f"""Generate comprehensive documentation for the following Python class:

**Class Information:**
- Name: {context.element_name}
- Signature: {context.signature}
- File: {context.file_path}

**Source Code:**
```python
{context.source_code}
```

**Existing Docstring:**
{context.docstring if context.docstring else "None"}

**Dependencies:** {', '.join(context.dependencies) if context.dependencies else 'None'}

**Decorators:** {', '.join(context.decorators) if context.decorators else 'None'}

Please generate documentation that includes:
1. A clear overview of the class purpose and functionality
2. Description of the class's role in the larger system
3. Usage examples showing how to instantiate and use the class
4. Important attributes and their purposes
5. Key methods and their roles (brief overview)
6. Inheritance information and relationships
7. Any design patterns or architectural considerations
8. Threading safety if relevant
9. Performance characteristics if relevant

Format the documentation as a complete docstring in {doc_style.value} style.
"""
        return prompt

    @staticmethod
    def get_method_prompt(context: DocumentationContext, doc_style: DocStyle = DocStyle.GOOGLE) -> str:
        """Generate prompt for documenting a class method."""

        prompt = f"""Generate comprehensive documentation for the following Python class method:

**Method Information:**
- Name: {context.element_name}
- Class: {context.parent_class}
- Signature: {context.signature}
- File: {context.file_path}
- Complexity Score: {context.complexity_score}

**Source Code:**
```python
{context.source_code}
```

**Existing Docstring:**
{context.docstring if context.docstring else "None"}

**Parameters:**
{DocumentationTemplates._format_parameters(context.parameters)}

**Return Type:** {context.return_type}

**Dependencies:** {', '.join(context.dependencies) if context.dependencies else 'None'}

**Decorators:** {', '.join(context.decorators) if context.decorators else 'None'}

Please generate documentation that includes:
1. Clear description of the method's purpose within the class context
2. Detailed parameter documentation
3. Return value documentation
4. Side effects on the object state
5. Exceptions that might be raised
6. Usage examples in the context of the class
7. Relationship to other methods in the class
8. Performance considerations if relevant

Format the documentation as a complete docstring in {doc_style.value} style.
"""
        return prompt

    @staticmethod
    def get_module_prompt(context: DocumentationContext, doc_style: DocStyle = DocStyle.GOOGLE) -> str:
        """Generate prompt for documenting a module."""

        prompt = f"""Generate comprehensive documentation for the following Python module:

**Module Information:**
- File: {context.file_path}
- Dependencies: {', '.join(context.dependencies) if context.dependencies else 'None'}

**Module Source Code:**
```python
{context.source_code}
```

**Existing Module Docstring:**
{context.docstring if context.docstring else "None"}

Please generate documentation that includes:
1. Clear overview of the module's purpose and functionality
2. Description of main components (classes, functions, constants)
3. How this module fits into the larger project
4. Usage examples and common patterns
5. Important constants or configuration variables
6. Dependencies and requirements
7. Installation or setup instructions if relevant
8. Examples of typical usage workflows

Format the documentation as a comprehensive module overview suitable for {doc_style.value} style.
"""
        return prompt

    @staticmethod
    def get_quality_assessment_prompt(documentation: str, context: DocumentationContext) -> str:
        """Generate prompt for assessing documentation quality."""

        return f"""Assess the quality of the following generated documentation and provide scores.

**Generated Documentation:**
{documentation}

**Original Code Context:**
- Element: {context.element_name} ({context.element_type})
- Signature: {context.signature}
- Complexity: {context.complexity_score}

Please evaluate the documentation on these criteria and provide scores from 0.0 to 1.0:

1. **Completeness** (0.0-1.0): Does the documentation cover all important aspects of the code?
   - Parameters, return values, exceptions documented
   - All functionality explained
   - Edge cases and limitations mentioned

2. **Clarity** (0.0-1.0): Is the documentation clear and easy to understand?
   - Well-structured and organized
   - Clear language and explanations
   - Good use of examples

3. **Accuracy** (0.0-1.0): Is the documentation factually correct?
   - Correctly describes what the code does
   - No assumptions or inaccuracies
   - Consistent with the actual implementation

4. **Usefulness** (0.0-1.0): How useful is this documentation for developers?
   - Provides practical guidance
   - Includes relevant examples
   - Helps developers understand usage

Respond with a JSON object containing the scores and brief explanations:
```json
{{
    "completeness_score": 0.0,
    "clarity_score": 0.0,
    "accuracy_score": 0.0,
    "usefulness_score": 0.0,
    "overall_score": 0.0,
    "feedback": {{
        "strengths": ["list", "of", "strengths"],
        "improvements": ["list", "of", "suggested", "improvements"],
        "missing_elements": ["list", "of", "missing", "information"]
    }}
}}
```
"""

    @staticmethod
    def _format_parameters(parameters: List[Dict[str, Any]]) -> str:
        """Format parameter list for display in prompts."""
        if not parameters:
            return "None"

        formatted = []
        for param in parameters:
            param_str = f"- {param['name']}: {param.get('type', 'Any')}"
            if not param.get('required', True):
                param_str += f" = {param.get('default', 'None')}"
            formatted.append(param_str)

        return "\n".join(formatted)

    @staticmethod
    def get_documentation_improvement_prompt(original_doc: str, feedback: Dict[str, Any]) -> str:
        """Generate prompt for improving documentation based on quality feedback."""

        return f"""Improve the following documentation based on the provided feedback:

**Original Documentation:**
{original_doc}

**Quality Feedback:**
- Completeness Score: {feedback.get('completeness_score', 0.0)}
- Clarity Score: {feedback.get('clarity_score', 0.0)}
- Accuracy Score: {feedback.get('accuracy_score', 0.0)}

**Specific Feedback:**
Strengths: {', '.join(feedback.get('feedback', {}).get('strengths', []))}
Improvements needed: {', '.join(feedback.get('feedback', {}).get('improvements', []))}
Missing elements: {', '.join(feedback.get('feedback', {}).get('missing_elements', []))}

Please rewrite the documentation to address the identified issues while preserving the strengths.
Focus particularly on the areas with lower scores and incorporate the suggested improvements.

Provide only the improved documentation without additional commentary.
"""