"""
Python AST Parser for extracting code structure.
Analyzes Python files and extracts functions, classes, methods, and other code elements.
"""

import ast
import inspect
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path
import hashlib

@dataclass
class CodeElement:
    """Represents a code element (function, class, method, etc.)"""
    element_type: str  # 'function', 'class', 'method', 'variable', 'import'
    name: str
    full_name: str
    signature: str
    docstring: str
    start_line: int
    end_line: int
    complexity_score: float
    dependencies: List[str]
    parameters: List[Dict[str, Any]]
    return_type: str
    visibility: str  # 'public', 'private', 'protected'
    is_async: bool
    is_static: bool
    is_abstract: bool
    decorators: List[str]
    parent_class: Optional[str] = None

@dataclass
class FileAnalysis:
    """Complete analysis of a Python file"""
    file_path: str
    content: str
    content_hash: str
    elements: List[CodeElement]
    imports: List[str]
    global_variables: List[str]
    line_count: int
    file_size: int

class PythonASTParser:
    """Parse Python code using AST and extract structure information."""

    def __init__(self):
        self.current_class = None
        self.imports = []
        self.complexity_weights = {
            'if': 1, 'for': 1, 'while': 1, 'try': 1,
            'except': 1, 'with': 1, 'and': 1, 'or': 1
        }

    def parse_file(self, file_path: str) -> FileAnalysis:
        """Parse a Python file and extract all code elements."""
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        content = path.read_text(encoding='utf-8')
        return self.parse_content(content, str(path))

    def parse_content(self, content: str, file_path: str = "unknown") -> FileAnalysis:
        """Parse Python content string and extract code elements."""
        try:
            tree = ast.parse(content)
        except SyntaxError as e:
            raise ValueError(f"Syntax error in {file_path}: {e}")

        # Reset state
        self.current_class = None
        self.imports = []

        # Extract elements
        elements = []
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                elements.append(self._extract_function(node))
            elif isinstance(node, ast.AsyncFunctionDef):
                elements.append(self._extract_function(node, is_async=True))
            elif isinstance(node, ast.ClassDef):
                elements.append(self._extract_class(node))
            elif isinstance(node, (ast.Import, ast.ImportFrom)):
                self._extract_imports(node)

        # Calculate file metadata
        content_hash = hashlib.sha256(content.encode()).hexdigest()
        line_count = content.count('\n') + 1
        file_size = len(content.encode())

        return FileAnalysis(
            file_path=file_path,
            content=content,
            content_hash=content_hash,
            elements=elements,
            imports=self.imports,
            global_variables=[],  # TODO: Extract global variables
            line_count=line_count,
            file_size=file_size
        )

    def _extract_function(self, node: ast.FunctionDef, is_async: bool = False) -> CodeElement:
        """Extract function/method information from AST node."""
        # Determine if this is a method (inside a class)
        element_type = "method" if self.current_class else "function"

        # Build full name
        full_name = f"{self.current_class}.{node.name}" if self.current_class else node.name

        # Extract signature
        signature = self._build_signature(node, is_async)

        # Extract docstring
        docstring = ast.get_docstring(node) or ""

        # Extract parameters
        parameters = self._extract_parameters(node.args)

        # Extract return type
        return_type = self._extract_return_type(node)

        # Determine visibility
        visibility = self._determine_visibility(node.name)

        # Extract decorators
        decorators = [self._get_decorator_name(dec) for dec in node.decorator_list]

        # Calculate complexity
        complexity = self._calculate_complexity(node)

        # Check if static/abstract
        is_static = any('staticmethod' in dec for dec in decorators)
        is_abstract = any('abstractmethod' in dec for dec in decorators)

        # Extract dependencies (function calls, attribute access)
        dependencies = self._extract_dependencies(node)

        return CodeElement(
            element_type=element_type,
            name=node.name,
            full_name=full_name,
            signature=signature,
            docstring=docstring,
            start_line=node.lineno,
            end_line=node.end_lineno or node.lineno,
            complexity_score=complexity,
            dependencies=dependencies,
            parameters=parameters,
            return_type=return_type,
            visibility=visibility,
            is_async=is_async,
            is_static=is_static,
            is_abstract=is_abstract,
            decorators=decorators,
            parent_class=self.current_class
        )

    def _extract_class(self, node: ast.ClassDef) -> CodeElement:
        """Extract class information from AST node."""
        # Save current class context
        old_class = self.current_class
        self.current_class = node.name

        # Extract docstring
        docstring = ast.get_docstring(node) or ""

        # Extract base classes
        base_classes = [self._get_name(base) for base in node.bases]
        dependencies = base_classes

        # Build signature
        if base_classes:
            signature = f"class {node.name}({', '.join(base_classes)}):"
        else:
            signature = f"class {node.name}:"

        # Extract decorators
        decorators = [self._get_decorator_name(dec) for dec in node.decorator_list]

        # Determine visibility
        visibility = self._determine_visibility(node.name)

        element = CodeElement(
            element_type="class",
            name=node.name,
            full_name=node.name,
            signature=signature,
            docstring=docstring,
            start_line=node.lineno,
            end_line=node.end_lineno or node.lineno,
            complexity_score=1.0,  # Base complexity for classes
            dependencies=dependencies,
            parameters=[],
            return_type="",
            visibility=visibility,
            is_async=False,
            is_static=False,
            is_abstract='ABC' in base_classes or any('abstract' in dec for dec in decorators),
            decorators=decorators
        )

        # Restore class context
        self.current_class = old_class
        return element

    def _build_signature(self, node: ast.FunctionDef, is_async: bool = False) -> str:
        """Build function signature string."""
        prefix = "async def" if is_async else "def"

        # Build arguments
        args = []

        # Regular arguments
        for arg in node.args.args:
            arg_str = arg.arg
            if arg.annotation:
                arg_str += f": {self._get_annotation(arg.annotation)}"
            args.append(arg_str)

        # Default arguments
        defaults = node.args.defaults
        if defaults:
            default_offset = len(args) - len(defaults)
            for i, default in enumerate(defaults):
                if default_offset + i < len(args):
                    args[default_offset + i] += f" = {self._get_default_value(default)}"

        # *args
        if node.args.vararg:
            vararg = f"*{node.args.vararg.arg}"
            if node.args.vararg.annotation:
                vararg += f": {self._get_annotation(node.args.vararg.annotation)}"
            args.append(vararg)

        # **kwargs
        if node.args.kwarg:
            kwarg = f"**{node.args.kwarg.arg}"
            if node.args.kwarg.annotation:
                kwarg += f": {self._get_annotation(node.args.kwarg.annotation)}"
            args.append(kwarg)

        signature = f"{prefix} {node.name}({', '.join(args)})"

        # Return type annotation
        if node.returns:
            signature += f" -> {self._get_annotation(node.returns)}"

        signature += ":"
        return signature

    def _extract_parameters(self, args: ast.arguments) -> List[Dict[str, Any]]:
        """Extract parameter information."""
        params = []

        for i, arg in enumerate(args.args):
            param = {
                'name': arg.arg,
                'type': self._get_annotation(arg.annotation) if arg.annotation else 'Any',
                'required': True,
                'default': None
            }

            # Check if has default value
            defaults = args.defaults
            if defaults and i >= len(args.args) - len(defaults):
                default_index = i - (len(args.args) - len(defaults))
                param['default'] = self._get_default_value(defaults[default_index])
                param['required'] = False

            params.append(param)

        return params

    def _extract_return_type(self, node: ast.FunctionDef) -> str:
        """Extract return type annotation."""
        if node.returns:
            return self._get_annotation(node.returns)
        return "Any"

    def _determine_visibility(self, name: str) -> str:
        """Determine visibility based on naming convention."""
        if name.startswith('__') and name.endswith('__'):
            return 'public'  # Magic methods are public
        elif name.startswith('__'):
            return 'private'
        elif name.startswith('_'):
            return 'protected'
        else:
            return 'public'

    def _calculate_complexity(self, node: ast.AST) -> float:
        """Calculate cyclomatic complexity of a function."""
        complexity = 1.0  # Base complexity

        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.For, ast.While, ast.Try, ast.With)):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                complexity += len(child.values) - 1
            elif isinstance(child, ast.ExceptHandler):
                complexity += 1

        return complexity

    def _extract_dependencies(self, node: ast.AST) -> List[str]:
        """Extract function calls and dependencies."""
        dependencies = set()

        for child in ast.walk(node):
            if isinstance(child, ast.Call):
                func_name = self._get_call_name(child.func)
                if func_name:
                    dependencies.add(func_name)
            elif isinstance(child, ast.Attribute):
                attr_name = self._get_attribute_chain(child)
                if attr_name:
                    dependencies.add(attr_name)

        return list(dependencies)

    def _extract_imports(self, node: ast.AST) -> None:
        """Extract import statements."""
        if isinstance(node, ast.Import):
            for alias in node.names:
                self.imports.append(alias.name)
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            for alias in node.names:
                if alias.name == "*":
                    self.imports.append(f"{module}.*")
                else:
                    self.imports.append(f"{module}.{alias.name}")

    def _get_decorator_name(self, decorator: ast.AST) -> str:
        """Get decorator name."""
        if isinstance(decorator, ast.Name):
            return decorator.id
        elif isinstance(decorator, ast.Attribute):
            return self._get_attribute_chain(decorator)
        elif isinstance(decorator, ast.Call):
            return self._get_call_name(decorator.func)
        return str(decorator)

    def _get_annotation(self, annotation: ast.AST) -> str:
        """Get type annotation as string."""
        if isinstance(annotation, ast.Name):
            return annotation.id
        elif isinstance(annotation, ast.Attribute):
            return self._get_attribute_chain(annotation)
        elif isinstance(annotation, ast.Subscript):
            return f"{self._get_annotation(annotation.value)}[{self._get_annotation(annotation.slice)}]"
        elif isinstance(annotation, ast.Constant):
            return repr(annotation.value)
        return "Any"

    def _get_default_value(self, default: ast.AST) -> str:
        """Get default value as string."""
        if isinstance(default, ast.Constant):
            return repr(default.value)
        elif isinstance(default, ast.Name):
            return default.id
        elif isinstance(default, ast.Attribute):
            return self._get_attribute_chain(default)
        return "..."

    def _get_name(self, node: ast.AST) -> str:
        """Get name from AST node."""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return self._get_attribute_chain(node)
        return str(node)

    def _get_call_name(self, func: ast.AST) -> str:
        """Get function call name."""
        if isinstance(func, ast.Name):
            return func.id
        elif isinstance(func, ast.Attribute):
            return self._get_attribute_chain(func)
        return ""

    def _get_attribute_chain(self, node: ast.Attribute) -> str:
        """Get full attribute chain (e.g., 'self.method' or 'module.function')."""
        parts = []
        current = node

        while isinstance(current, ast.Attribute):
            parts.append(current.attr)
            current = current.value

        if isinstance(current, ast.Name):
            parts.append(current.id)

        return '.'.join(reversed(parts))

# Example usage function
def analyze_python_file(file_path: str) -> FileAnalysis:
    """Convenience function to analyze a Python file."""
    parser = PythonASTParser()
    return parser.parse_file(file_path)