# Code-to-Documentation AI Agent System Design

## Overview

This document outlines the design for an AI agent system that converts code to documentation using LangGraph orchestration and PostgreSQL vector storage for RAG capabilities.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    LangGraph Orchestrator                      │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐    ┌──────────────┐    ┌─────────────────┐    │
│  │   Code      │    │ Documentation│    │   Embedding     │    │
│  │ Analyzer    │───▶│  Generator   │───▶│ & Chunking      │    │
│  │   Agent     │    │    Agent     │    │    Agent        │    │
│  └─────────────┘    └──────────────┘    └─────────────────┘    │
│         │                   │                       │          │
│         ▼                   ▼                       ▼          │
│  ┌─────────────┐    ┌──────────────┐    ┌─────────────────┐    │
│  │  Metadata   │    │   Quality    │    │  PostgreSQL     │    │
│  │ Extractor   │    │  Validator   │    │   Vector        │    │
│  │   Agent     │    │    Agent     │    │   Storage       │    │
│  └─────────────┘    └──────────────┘    └─────────────────┘    │
│                                                 │               │
│         ┌───────────────────────────────────────┘               │
│         ▼                                                       │
│  ┌─────────────┐    ┌──────────────┐                           │
│  │   Search    │    │  Retrieval   │                           │
│  │ & Query     │◀───│   Agent      │                           │
│  │   Agent     │    │              │                           │
│  └─────────────┘    └──────────────┘                           │
└─────────────────────────────────────────────────────────────────┘
```

## System Components

### 1. PostgreSQL Vector Database Schema

#### Core Tables:

```sql
-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Projects table
CREATE TABLE projects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    repository_url VARCHAR(500),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Code files table
CREATE TABLE code_files (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
    file_path VARCHAR(1000) NOT NULL,
    file_type VARCHAR(50), -- 'python', 'javascript', 'java', etc.
    content TEXT NOT NULL,
    content_hash VARCHAR(64), -- SHA256 hash for change detection
    last_analyzed TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(project_id, file_path)
);

-- Code elements (functions, classes, modules, etc.)
CREATE TABLE code_elements (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    file_id UUID REFERENCES code_files(id) ON DELETE CASCADE,
    element_type VARCHAR(50), -- 'function', 'class', 'method', 'variable', 'module'
    name VARCHAR(255) NOT NULL,
    signature TEXT, -- Function signatures, class definitions
    docstring TEXT, -- Existing docstrings
    start_line INTEGER,
    end_line INTEGER,
    complexity_score FLOAT, -- Cyclomatic complexity
    dependencies JSONB, -- List of dependencies/imports
    metadata JSONB, -- Additional metadata (parameters, return types, etc.)
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Generated documentation
CREATE TABLE documentation (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    element_id UUID REFERENCES code_elements(id) ON DELETE CASCADE,
    doc_type VARCHAR(50), -- 'overview', 'api', 'tutorial', 'example'
    title VARCHAR(500),
    content TEXT NOT NULL,
    generated_by VARCHAR(100), -- Which LLM/agent generated this
    quality_score FLOAT, -- Quality assessment score
    human_reviewed BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Vector embeddings for semantic search
CREATE TABLE document_embeddings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    documentation_id UUID REFERENCES documentation(id) ON DELETE CASCADE,
    chunk_index INTEGER, -- For document chunking
    chunk_text TEXT NOT NULL,
    embedding vector(1536), -- OpenAI ada-002 dimensions
    metadata JSONB, -- Chunk metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Search and query logs
CREATE TABLE search_queries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID REFERENCES projects(id),
    query_text TEXT NOT NULL,
    query_embedding vector(1536),
    results_found INTEGER,
    response_time_ms INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for performance
CREATE INDEX idx_code_files_project_type ON code_files(project_id, file_type);
CREATE INDEX idx_code_elements_file_type ON code_elements(file_id, element_type);
CREATE INDEX idx_doc_embeddings_vector ON document_embeddings USING ivfflat (embedding vector_cosine_ops);
CREATE INDEX idx_search_queries_embedding ON search_queries USING ivfflat (query_embedding vector_cosine_ops);
```

### 2. LangGraph Agent Architecture

#### Agent State Definition:
```python
from typing import Dict, List, Optional, TypedDict
from dataclasses import dataclass

class CodeAnalysisState(TypedDict):
    # Input
    project_id: str
    file_path: str
    file_content: str

    # Analysis Results
    parsed_ast: Dict
    code_elements: List[Dict]
    dependencies: List[str]
    complexity_metrics: Dict

    # Documentation Generation
    generated_docs: List[Dict]
    doc_quality_scores: List[float]

    # Vector Storage
    embeddings: List[List[float]]
    chunk_mappings: List[Dict]
    storage_ids: List[str]

    # Search & Retrieval
    search_query: Optional[str]
    search_results: List[Dict]

    # Workflow State
    current_step: str
    errors: List[str]
    warnings: List[str]
```

#### Core Agents:

1. **Code Analyzer Agent**
   - Parse AST using `ast` (Python) or `tree-sitter` (multi-language)
   - Extract functions, classes, methods, variables
   - Calculate complexity metrics
   - Identify dependencies and imports

2. **Metadata Extractor Agent**
   - Extract type hints and annotations
   - Analyze function signatures
   - Identify design patterns
   - Extract existing docstrings

3. **Documentation Generator Agent**
   - Generate comprehensive documentation using LLM
   - Create multiple doc types (API docs, tutorials, examples)
   - Follow documentation standards (Google, NumPy, Sphinx styles)

4. **Quality Validator Agent**
   - Assess documentation quality
   - Check for completeness
   - Validate examples and code snippets
   - Score documentation usefulness

5. **Embedding & Chunking Agent**
   - Split documents into semantic chunks
   - Generate embeddings using OpenAI or local models
   - Store vectors in PostgreSQL

6. **Search & Retrieval Agent**
   - Semantic search using vector similarity
   - Hybrid search (semantic + keyword)
   - Context ranking and reranking

### 3. Technology Stack

#### Core Dependencies:
```python
# LangGraph and LangChain
langgraph>=0.0.40
langchain>=0.1.0
langchain-openai
langchain-community

# Database and Vector Storage
psycopg2-binary>=2.9.0
pgvector>=0.2.0
sqlalchemy>=2.0.0
alembic  # Database migrations

# Code Analysis
ast  # Built-in Python AST
tree-sitter>=0.20.0
tree-sitter-python
tree-sitter-javascript
gitpython

# Embeddings and ML
openai>=1.0.0
sentence-transformers  # Alternative to OpenAI
numpy>=1.24.0

# Text Processing
tiktoken  # Token counting
nltk  # Text processing
spacy  # NLP processing

# API and Web
fastapi>=0.100.0
uvicorn
streamlit  # Demo interface
pydantic>=2.0.0

# Utilities
python-dotenv
pyyaml
rich  # Beautiful terminal output
```

### 4. Document Chunking Strategy

#### Semantic Chunking Approach:
```python
class DocumentChunker:
    def __init__(self, chunk_size: int = 1000, overlap: int = 200):
        self.chunk_size = chunk_size
        self.overlap = overlap

    def chunk_by_code_structure(self, content: str, elements: List[Dict]) -> List[Dict]:
        """Chunk based on code structure (functions, classes)"""
        pass

    def chunk_by_semantic_similarity(self, content: str) -> List[Dict]:
        """Chunk based on semantic similarity between sentences"""
        pass

    def adaptive_chunking(self, content: str, content_type: str) -> List[Dict]:
        """Adaptive chunking based on content type"""
        pass
```

### 5. Search and Retrieval Strategy

#### Multi-Modal Search:
```python
class SearchStrategy:
    def semantic_search(self, query: str, limit: int = 10) -> List[Dict]:
        """Vector similarity search"""
        pass

    def keyword_search(self, query: str, limit: int = 10) -> List[Dict]:
        """Full-text search"""
        pass

    def hybrid_search(self, query: str, semantic_weight: float = 0.7) -> List[Dict]:
        """Combine semantic and keyword search"""
        pass

    def contextual_rerank(self, results: List[Dict], context: str) -> List[Dict]:
        """Rerank results based on context"""
        pass
```

## Implementation Roadmap

### Phase 1: Foundation (Week 1-2)
1. Set up PostgreSQL with pgvector
2. Create database schema and migrations
3. Implement basic LangGraph workflow
4. Build Code Analyzer Agent

### Phase 2: Core Features (Week 2-3)
1. Implement Documentation Generator Agent
2. Add Embedding & Chunking Agent
3. Create PostgreSQL vector storage layer
4. Build basic search functionality

### Phase 3: Enhancement (Week 3-4)
1. Add Quality Validator Agent
2. Implement hybrid search
3. Create demo interface
4. Add comprehensive testing

### Phase 4: RAGFlow Integration (Week 4-5)
1. Create RAGFlow integration layer
2. Implement comparison framework
3. Build unified demo interface
4. Performance benchmarking

## Configuration and Environment

### Environment Variables:
```bash
# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/code_to_doc
PGVECTOR_ENABLED=true

# OpenAI (or alternative)
OPENAI_API_KEY=your_key_here
EMBEDDING_MODEL=text-embedding-ada-002
COMPLETION_MODEL=gpt-4

# LangGraph
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=your_langsmith_key

# Application
LOG_LEVEL=INFO
CHUNK_SIZE=1000
CHUNK_OVERLAP=200
```

This design provides a solid foundation for understanding RAG internals before moving to RAGFlow. Would you like me to start implementing any specific component first?