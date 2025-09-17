"""
Database utilities and helpers for the code-to-documentation system.
Provides convenient functions for common database operations.
"""

import os
import psycopg2
import psycopg2.extras
from contextlib import contextmanager
from typing import List, Dict, Any, Optional, Tuple
import hashlib
import json
from dataclasses import dataclass
from datetime import datetime
import numpy as np

# Database configuration
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': int(os.getenv('DB_PORT', 5432)),
    'database': os.getenv('DB_NAME', 'code_to_doc'),
    'user': os.getenv('DB_USER', os.getenv('USER')),
    'password': os.getenv('DB_PASSWORD', '')
}

@dataclass
class Project:
    """Project data model."""
    id: str
    name: str
    description: str
    repository_url: str
    language: str
    framework: str
    documentation_style: str
    created_at: datetime
    updated_at: datetime

@dataclass
class CodeFile:
    """Code file data model."""
    id: str
    project_id: str
    file_path: str
    file_type: str
    content: str
    content_hash: str
    file_size: int
    line_count: int
    last_analyzed: Optional[datetime]
    analysis_version: Optional[str]
    created_at: datetime
    updated_at: datetime

@dataclass
class CodeElement:
    """Code element data model."""
    id: str
    file_id: str
    element_type: str
    name: str
    full_name: str
    signature: str
    docstring: str
    start_line: int
    end_line: int
    complexity_score: float
    dependencies: List[str]
    parameters: List[Dict]
    return_type: str
    decorators: List[str]
    visibility: str
    is_async: bool
    is_static: bool
    is_abstract: bool
    metadata: Dict
    created_at: datetime

@dataclass
class Documentation:
    """Documentation data model."""
    id: str
    element_id: Optional[str]
    project_id: Optional[str]
    doc_type: str
    title: str
    content: str
    generated_by: str
    quality_score: float
    approved: bool
    word_count: int
    created_at: datetime
    updated_at: datetime

class DatabaseManager:
    """Database connection and operation manager."""

    def __init__(self, config: Dict = None):
        self.config = config or DB_CONFIG

    @contextmanager
    def get_connection(self):
        """Get a database connection with automatic cleanup."""
        conn = None
        try:
            conn = psycopg2.connect(**self.config)
            yield conn
        finally:
            if conn:
                conn.close()

    @contextmanager
    def get_cursor(self, dict_cursor=True):
        """Get a database cursor with automatic cleanup."""
        with self.get_connection() as conn:
            cursor_factory = psycopg2.extras.RealDictCursor if dict_cursor else None
            cursor = conn.cursor(cursor_factory=cursor_factory)
            try:
                yield cursor, conn
            finally:
                cursor.close()

class ProjectManager:
    """Manage project-related database operations."""

    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager

    def create_project(self, name: str, description: str = "", repository_url: str = "",
                      language: str = "", framework: str = "",
                      documentation_style: str = "google") -> str:
        """Create a new project and return its ID."""
        with self.db.get_cursor() as (cursor, conn):
            cursor.execute("""
                INSERT INTO projects (name, description, repository_url, language, framework, documentation_style)
                VALUES (%(name)s, %(description)s, %(repository_url)s, %(language)s, %(framework)s, %(documentation_style)s)
                RETURNING id
            """, {
                'name': name,
                'description': description,
                'repository_url': repository_url,
                'language': language,
                'framework': framework,
                'documentation_style': documentation_style
            })
            project_id = cursor.fetchone()['id']
            conn.commit()
            return str(project_id)

    def get_project(self, project_id: str) -> Optional[Project]:
        """Get a project by ID."""
        with self.db.get_cursor() as (cursor, conn):
            cursor.execute("SELECT * FROM projects WHERE id = %s", (project_id,))
            row = cursor.fetchone()
            if row:
                return Project(**row)
            return None

    def list_projects(self) -> List[Project]:
        """List all projects."""
        with self.db.get_cursor() as (cursor, conn):
            cursor.execute("SELECT * FROM projects ORDER BY created_at DESC")
            return [Project(**row) for row in cursor.fetchall()]

class CodeFileManager:
    """Manage code file-related database operations."""

    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager

    def add_file(self, project_id: str, file_path: str, content: str,
                file_type: str) -> str:
        """Add a code file to the database."""
        content_hash = hashlib.sha256(content.encode()).hexdigest()
        file_size = len(content.encode())
        line_count = content.count('\n') + 1

        with self.db.get_cursor() as (cursor, conn):
            cursor.execute("""
                INSERT INTO code_files (project_id, file_path, file_type, content,
                                      content_hash, file_size, line_count)
                VALUES (%(project_id)s, %(file_path)s, %(file_type)s, %(content)s,
                       %(content_hash)s, %(file_size)s, %(line_count)s)
                ON CONFLICT (project_id, file_path)
                DO UPDATE SET
                    content = EXCLUDED.content,
                    content_hash = EXCLUDED.content_hash,
                    file_size = EXCLUDED.file_size,
                    line_count = EXCLUDED.line_count,
                    updated_at = CURRENT_TIMESTAMP
                RETURNING id
            """, {
                'project_id': project_id,
                'file_path': file_path,
                'file_type': file_type,
                'content': content,
                'content_hash': content_hash,
                'file_size': file_size,
                'line_count': line_count
            })
            file_id = cursor.fetchone()['id']
            conn.commit()
            return str(file_id)

    def get_files_for_project(self, project_id: str) -> List[CodeFile]:
        """Get all files for a project."""
        with self.db.get_cursor() as (cursor, conn):
            cursor.execute("""
                SELECT * FROM code_files
                WHERE project_id = %s
                ORDER BY file_path
            """, (project_id,))
            return [CodeFile(**row) for row in cursor.fetchall()]

    def file_needs_analysis(self, file_id: str, content_hash: str) -> bool:
        """Check if a file needs re-analysis based on content hash."""
        with self.db.get_cursor() as (cursor, conn):
            cursor.execute("""
                SELECT content_hash, last_analyzed
                FROM code_files
                WHERE id = %s
            """, (file_id,))
            row = cursor.fetchone()
            if not row:
                return True

            return (row['content_hash'] != content_hash or
                   row['last_analyzed'] is None)

class CodeElementManager:
    """Manage code element-related database operations."""

    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager

    def add_element(self, file_id: str, element_type: str, name: str,
                   full_name: str, signature: str, docstring: str = "",
                   start_line: int = 0, end_line: int = 0,
                   complexity_score: float = 1.0, dependencies: List[str] = None,
                   parameters: List[Dict] = None, return_type: str = "",
                   visibility: str = "public") -> str:
        """Add a code element to the database."""

        dependencies = dependencies or []
        parameters = parameters or []

        with self.db.get_cursor() as (cursor, conn):
            cursor.execute("""
                INSERT INTO code_elements (
                    file_id, element_type, name, full_name, signature, docstring,
                    start_line, end_line, complexity_score, dependencies,
                    parameters, return_type, visibility
                ) VALUES (
                    %(file_id)s, %(element_type)s, %(name)s, %(full_name)s,
                    %(signature)s, %(docstring)s, %(start_line)s, %(end_line)s,
                    %(complexity_score)s, %(dependencies)s, %(parameters)s,
                    %(return_type)s, %(visibility)s
                )
                RETURNING id
            """, {
                'file_id': file_id,
                'element_type': element_type,
                'name': name,
                'full_name': full_name,
                'signature': signature,
                'docstring': docstring,
                'start_line': start_line,
                'end_line': end_line,
                'complexity_score': complexity_score,
                'dependencies': json.dumps(dependencies),
                'parameters': json.dumps(parameters),
                'return_type': return_type,
                'visibility': visibility
            })
            element_id = cursor.fetchone()['id']
            conn.commit()
            return str(element_id)

    def get_elements_for_file(self, file_id: str) -> List[CodeElement]:
        """Get all code elements for a file."""
        with self.db.get_cursor() as (cursor, conn):
            cursor.execute("""
                SELECT * FROM code_elements
                WHERE file_id = %s
                ORDER BY start_line
            """, (file_id,))
            elements = []
            for row in cursor.fetchall():
                # Convert to dict and handle JSON fields
                row_dict = dict(row)

                # Handle JSON fields - they might already be parsed
                json_fields = ['dependencies', 'parameters', 'decorators', 'metadata']
                for field in json_fields:
                    if field in row_dict and isinstance(row_dict[field], str):
                        row_dict[field] = json.loads(row_dict[field])

                elements.append(CodeElement(**row_dict))
            return elements

    def get_element_by_id(self, element_id: str) -> Optional[CodeElement]:
        """Get a single code element by ID."""
        with self.db.get_cursor() as (cursor, conn):
            cursor.execute("""
                SELECT * FROM code_elements
                WHERE id = %s
            """, (element_id,))
            row = cursor.fetchone()
            if row:
                # Convert to dict and handle JSON fields
                row_dict = dict(row)

                # Handle JSON fields - they might already be parsed
                json_fields = ['dependencies', 'parameters', 'decorators', 'metadata']
                for field in json_fields:
                    if field in row_dict and isinstance(row_dict[field], str):
                        row_dict[field] = json.loads(row_dict[field])

                return CodeElement(**row_dict)
            return None

class DocumentationManager:
    """Manage documentation-related database operations."""

    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager

    def add_documentation(self, element_id: str, doc_type: str, title: str,
                         content: str, generated_by: str, quality_score: float = 0.0,
                         completeness_score: float = 0.0, clarity_score: float = 0.0,
                         accuracy_score: float = 0.0) -> str:
        """Add documentation for a code element."""
        word_count = len(content.split())

        with self.db.get_cursor() as (cursor, conn):
            cursor.execute("""
                INSERT INTO documentation (
                    element_id, doc_type, title, content, generated_by,
                    quality_score, completeness_score, clarity_score,
                    accuracy_score, word_count
                ) VALUES (
                    %(element_id)s, %(doc_type)s, %(title)s, %(content)s,
                    %(generated_by)s, %(quality_score)s, %(completeness_score)s,
                    %(clarity_score)s, %(accuracy_score)s, %(word_count)s
                )
                RETURNING id
            """, {
                'element_id': element_id,
                'doc_type': doc_type,
                'title': title,
                'content': content,
                'generated_by': generated_by,
                'quality_score': quality_score,
                'completeness_score': completeness_score,
                'clarity_score': clarity_score,
                'accuracy_score': accuracy_score,
                'word_count': word_count
            })
            doc_id = cursor.fetchone()['id']
            conn.commit()
            return str(doc_id)

    def add_embedding(self, documentation_id: str, chunk_index: int,
                     chunk_text: str, embedding: List[float],
                     embedding_model: str = "text-embedding-ada-002") -> str:
        """Add an embedding for a documentation chunk."""
        token_count = len(chunk_text.split())
        char_count = len(chunk_text)

        with self.db.get_cursor() as (cursor, conn):
            # Convert embedding list to PostgreSQL vector format
            embedding_str = '[' + ','.join(map(str, embedding)) + ']'

            cursor.execute("""
                INSERT INTO document_embeddings (
                    documentation_id, chunk_index, chunk_text, embedding,
                    embedding_model, token_count, char_count
                ) VALUES (
                    %(documentation_id)s, %(chunk_index)s, %(chunk_text)s,
                    %(embedding)s::vector, %(embedding_model)s, %(token_count)s, %(char_count)s
                )
                ON CONFLICT (documentation_id, chunk_index)
                DO UPDATE SET
                    chunk_text = EXCLUDED.chunk_text,
                    embedding = EXCLUDED.embedding,
                    embedding_model = EXCLUDED.embedding_model,
                    token_count = EXCLUDED.token_count,
                    char_count = EXCLUDED.char_count
                RETURNING id
            """, {
                'documentation_id': documentation_id,
                'chunk_index': chunk_index,
                'chunk_text': chunk_text,
                'embedding': embedding_str,
                'embedding_model': embedding_model,
                'token_count': token_count,
                'char_count': char_count
            })
            embedding_id = cursor.fetchone()['id']
            conn.commit()
            return str(embedding_id)

class SearchManager:
    """Manage search and retrieval operations."""

    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager

    def semantic_search(self, query_embedding: List[float], project_id: str = None,
                       limit: int = 10, similarity_threshold: float = 0.7) -> List[Dict]:
        """Perform semantic search using vector similarity."""
        embedding_str = '[' + ','.join(map(str, query_embedding)) + ']'

        with self.db.get_cursor() as (cursor, conn):
            if project_id:
                cursor.execute("""
                    SELECT
                        de.chunk_text,
                        d.title,
                        d.content,
                        ce.name as element_name,
                        ce.element_type,
                        cf.file_path,
                        1 - (de.embedding <=> %s::vector) as similarity
                    FROM document_embeddings de
                    JOIN documentation d ON de.documentation_id = d.id
                    JOIN code_elements ce ON d.element_id = ce.id
                    JOIN code_files cf ON ce.file_id = cf.id
                    WHERE cf.project_id = %s
                      AND 1 - (de.embedding <=> %s::vector) > %s
                    ORDER BY de.embedding <=> %s::vector
                    LIMIT %s
                """, (embedding_str, project_id, embedding_str,
                     similarity_threshold, embedding_str, limit))
            else:
                cursor.execute("""
                    SELECT
                        de.chunk_text,
                        d.title,
                        d.content,
                        ce.name as element_name,
                        ce.element_type,
                        cf.file_path,
                        1 - (de.embedding <=> %s::vector) as similarity
                    FROM document_embeddings de
                    JOIN documentation d ON de.documentation_id = d.id
                    JOIN code_elements ce ON d.element_id = ce.id
                    JOIN code_files cf ON ce.file_id = cf.id
                    WHERE 1 - (de.embedding <=> %s::vector) > %s
                    ORDER BY de.embedding <=> %s::vector
                    LIMIT %s
                """, (embedding_str, embedding_str, similarity_threshold,
                     embedding_str, limit))

            return [dict(row) for row in cursor.fetchall()]

    def log_search_query(self, query_text: str, project_id: str = None,
                        query_type: str = "semantic", results_found: int = 0,
                        response_time_ms: int = 0) -> str:
        """Log a search query for analytics."""
        with self.db.get_cursor() as (cursor, conn):
            cursor.execute("""
                INSERT INTO search_queries (
                    project_id, query_text, query_type, results_found, response_time_ms
                ) VALUES (
                    %(project_id)s, %(query_text)s, %(query_type)s,
                    %(results_found)s, %(response_time_ms)s
                )
                RETURNING id
            """, {
                'project_id': project_id,
                'query_text': query_text,
                'query_type': query_type,
                'results_found': results_found,
                'response_time_ms': response_time_ms
            })
            query_id = cursor.fetchone()['id']
            conn.commit()
            return str(query_id)

# Convenience functions
def get_db_manager() -> DatabaseManager:
    """Get a database manager instance."""
    return DatabaseManager()

def get_project_manager() -> ProjectManager:
    """Get a project manager instance."""
    return ProjectManager(get_db_manager())

def get_code_file_manager() -> CodeFileManager:
    """Get a code file manager instance."""
    return CodeFileManager(get_db_manager())

def get_code_element_manager() -> CodeElementManager:
    """Get a code element manager instance."""
    return CodeElementManager(get_db_manager())

def get_documentation_manager() -> DocumentationManager:
    """Get a documentation manager instance."""
    return DocumentationManager(get_db_manager())

def get_search_manager() -> SearchManager:
    """Get a search manager instance."""
    return SearchManager(get_db_manager())