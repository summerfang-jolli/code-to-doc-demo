# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.


## Project Overview

This is a **Code-to-Documentation AI Agent System** that uses LangGraph to orchestrate the conversion of source code into comprehensive documentation, with PostgreSQL vector storage for RAG capabilities.

### Architecture
- **LangGraph** for multi-agent workflow orchestration
- **PostgreSQL + pgvector** for vector storage and semantic search
- **OpenAI** for embeddings and documentation generation
- **Custom RAG pipeline** (Phase 1) followed by **RAGFlow integration** (Phase 2)

## Key Components

### Agents
- **Code Analyzer Agent**: Parses AST, extracts functions/classes/methods
- **Documentation Generator Agent**: Creates comprehensive docs using LLM
- **Embedding & Chunking Agent**: Splits docs and generates vectors
- **Search & Retrieval Agent**: Semantic search with PostgreSQL vectors
- **Quality Validator Agent**: Assesses and scores documentation quality

### Database Schema
- `projects`, `code_files`, `code_elements` - Code structure storage
- `documentation`, `document_embeddings` - Generated docs and vectors
- Uses pgvector extension for efficient similarity search

## Development Commands

### Database Setup
```bash
# Install PostgreSQL with pgvector
# Create database and run migrations
python -m alembic upgrade head
```

### Development
```bash
# Install dependencies
pip install -r requirements.txt

# Run the application
python src/main.py

# Run tests
pytest tests/

# Start demo interface
streamlit run demo/streamlit_app.py
```

## Implementation Phases

1. **Phase 1**: Custom RAG with PostgreSQL vectors
2. **Phase 2**: RAGFlow integration for comparison
3. **Phase 3**: Unified demo interface

## Key Files
- `DESIGN.md` - Comprehensive system design document
- `src/workflow/graph.py` - LangGraph workflow definition
- `src/agents/` - Individual agent implementations
- `database/schema.sql` - PostgreSQL schema with pgvector
