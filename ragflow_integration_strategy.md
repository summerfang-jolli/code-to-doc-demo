# RAGFlow Integration Strategy for Function Docstrings

## Overview
This document outlines the recommended approach for storing function signatures and docstrings in RAGFlow for optimal retrieval and search capabilities.

## Storage Strategy

### 1. Document Structure
Each function should be stored as a separate document with:

```json
{
  "id": "filename.py:function_name",
  "title": "function_name - filename.py",
  "content": "Combined signature + docstring + metadata",
  "metadata": {
    "file_path": "src/agents/code_analyzer.py",
    "function_name": "analyze_code",
    "signature": "def analyze_code(self, content: str) -> Dict[str, Any]:",
    "element_type": "method",
    "parent_class": "CodeAnalyzer",
    "complexity_score": 3.5,
    "parameters": [...],
    "return_type": "Dict[str, Any]"
  }
}
```

### 2. Content Format
Combine signature and docstring for rich context:

```
Function: analyze_code
Signature: def analyze_code(self, content: str) -> Dict[str, Any]:
File: src/agents/code_analyzer.py
Type: method
Class: CodeAnalyzer
Parameters: content: str
Returns: Dict[str, Any]
Complexity: 3.5

Documentation:
Analyze Python source code and extract structural information.

This method parses the provided code content using AST analysis
to identify functions, classes, methods, and their relationships.

Args:
    content (str): The Python source code to analyze

Returns:
    Dict[str, Any]: Analysis results containing:
        - functions: List of function definitions
        - classes: List of class definitions
        - imports: List of import statements
        - complexity_metrics: Code complexity analysis
```

### 3. RAGFlow Configuration

#### Knowledge Base Setup
1. **Collection Name**: `code_docstrings`
2. **Chunking Strategy**:
   - **Method**: Manual (one function per document)
   - **Chunk Size**: Variable (based on function length)
   - **Overlap**: 0 (functions are discrete units)

#### Parsing Configuration
```json
{
  "chunk_token_count": 1024,
  "layout_recognize": false,
  "task_page_size": 12,
  "parser_config": {
    "chunk_token_num": 1024,
    "delimiter": "\n\n",
    "layout_recognize": false,
    "task_page_size": 12
  }
}
```

#### Embedding Model
- **Recommended**: `text-embedding-3-small` or `text-embedding-ada-002`
- **Reason**: Good balance of speed and quality for code documentation

### 4. Search Optimization

#### Query Types to Support
1. **Function Name Search**: "find function parse_content"
2. **Functionality Search**: "how to analyze Python AST"
3. **Parameter Search**: "functions that take file_path parameter"
4. **Return Type Search**: "functions returning Dict"
5. **Class Method Search**: "methods in CodeAnalyzer class"

#### Metadata Filters
Enable filtering by:
- `file_path`: Search within specific files
- `element_type`: Filter by function/method/class
- `parent_class`: Find methods in specific classes
- `complexity_score`: Find simple/complex functions
- `is_async`: Find async functions

### 5. Upload Process

#### Using the extraction script:
```bash
# Extract from entire src directory
python extract_docstrings.py -i src/ -r --ragflow-output ragflow_docs.json

# Upload to RAGFlow via API
curl -X POST "http://ragflow-server/api/v1/datasets/{dataset_id}/documents" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d @ragflow_docs.json
```

#### Batch Processing
For large codebases:
1. Process files in batches of 100-500 functions
2. Use parallel processing for multiple files
3. Implement retry logic for failed uploads

### 6. Query Examples

#### RAGFlow Chat Interface
```
User: "How do I parse Python code using AST?"
RAGFlow: [Returns functions related to AST parsing with their signatures and docstrings]

User: "Show me async functions in the codebase"
RAGFlow: [Filters by is_async=true metadata and returns matching functions]

User: "What functions take a file_path parameter?"
RAGFlow: [Searches parameter metadata and content for file_path usage]
```

#### API Queries
```json
{
  "query": "extract function information from AST",
  "filters": {
    "element_type": "function",
    "complexity_score": {"$lt": 5.0}
  },
  "limit": 10
}
```

### 7. Maintenance Strategy

#### Regular Updates
1. **Incremental Updates**: Track file modification times
2. **Hash-based Changes**: Compare content hashes to detect changes
3. **Automated Pipeline**: CI/CD integration for documentation updates

#### Version Control
- Link documents to specific git commits
- Maintain historical versions of function documentation
- Track documentation evolution over time

## Implementation Steps

1. **Setup RAGFlow instance** with appropriate configuration
2. **Run extraction script** on your codebase
3. **Upload initial dataset** to RAGFlow
4. **Configure search interface** with metadata filters
5. **Test query patterns** for your use cases
6. **Setup automated updates** for code changes

## Benefits

1. **Unified Search**: Find functions by name, functionality, or signature
2. **Context-Aware**: Combines signature with documentation for better understanding
3. **Metadata-Rich**: Enables complex filtering and categorization
4. **Scalable**: Handles large codebases efficiently
5. **Version-Tracked**: Maintains documentation history