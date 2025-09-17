-- Code-to-Documentation Database Schema
-- PostgreSQL with pgvector extension

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Enable RLS (Row Level Security) for future multi-tenancy if needed
-- ALTER DATABASE code_to_doc SET row_security = on;

-- ============================================================================
-- CORE TABLES
-- ============================================================================

-- Projects table - Root level organization
CREATE TABLE projects (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    repository_url VARCHAR(500),
    repository_type VARCHAR(50) DEFAULT 'git', -- 'git', 'local', 'url'
    language VARCHAR(50), -- Primary language: 'python', 'javascript', 'java', etc.
    framework VARCHAR(100), -- Framework if applicable: 'django', 'react', 'spring', etc.
    documentation_style VARCHAR(50) DEFAULT 'google', -- 'google', 'numpy', 'sphinx'
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Code files table - Individual source files
CREATE TABLE code_files (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    file_path VARCHAR(1000) NOT NULL,
    file_type VARCHAR(50) NOT NULL, -- 'python', 'javascript', 'java', 'typescript', etc.
    content TEXT NOT NULL,
    content_hash VARCHAR(64) NOT NULL, -- SHA256 hash for change detection
    file_size INTEGER, -- File size in bytes
    line_count INTEGER, -- Number of lines
    last_analyzed TIMESTAMP WITH TIME ZONE,
    analysis_version VARCHAR(20), -- Track which version of analyzer was used
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(project_id, file_path)
);

-- Code elements - Functions, classes, methods, modules, variables
CREATE TABLE code_elements (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    file_id UUID NOT NULL REFERENCES code_files(id) ON DELETE CASCADE,
    element_type VARCHAR(50) NOT NULL, -- 'function', 'class', 'method', 'variable', 'module', 'import'
    name VARCHAR(255) NOT NULL,
    full_name VARCHAR(500), -- Fully qualified name including module/class path
    signature TEXT, -- Function signatures, class definitions
    docstring TEXT, -- Existing docstrings/comments
    start_line INTEGER NOT NULL,
    end_line INTEGER NOT NULL,
    complexity_score FLOAT, -- Cyclomatic complexity or similar
    dependencies JSONB DEFAULT '[]'::jsonb, -- List of dependencies/imports
    parameters JSONB DEFAULT '[]'::jsonb, -- Function/method parameters
    return_type VARCHAR(100), -- Return type if available
    decorators JSONB DEFAULT '[]'::jsonb, -- Python decorators or annotations
    visibility VARCHAR(20) DEFAULT 'public', -- 'public', 'private', 'protected'
    is_async BOOLEAN DEFAULT FALSE, -- For async functions
    is_static BOOLEAN DEFAULT FALSE, -- For static methods
    is_abstract BOOLEAN DEFAULT FALSE, -- For abstract methods/classes
    metadata JSONB DEFAULT '{}'::jsonb, -- Additional metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Generated documentation
CREATE TABLE documentation (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    element_id UUID REFERENCES code_elements(id) ON DELETE CASCADE,
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE, -- For project-level docs
    doc_type VARCHAR(50) NOT NULL, -- 'api', 'tutorial', 'overview', 'example', 'troubleshooting'
    title VARCHAR(500) NOT NULL,
    content TEXT NOT NULL,
    content_format VARCHAR(20) DEFAULT 'markdown', -- 'markdown', 'rst', 'html'
    generated_by VARCHAR(100) NOT NULL, -- Which LLM/agent generated this
    model_version VARCHAR(50), -- Model version used
    quality_score FLOAT, -- Quality assessment score (0-1)
    completeness_score FLOAT, -- How complete the documentation is (0-1)
    clarity_score FLOAT, -- How clear/readable it is (0-1)
    accuracy_score FLOAT, -- How accurate it is (0-1)
    human_reviewed BOOLEAN DEFAULT FALSE,
    human_feedback TEXT, -- Human reviewer feedback
    review_date TIMESTAMP WITH TIME ZONE,
    approved BOOLEAN DEFAULT FALSE,
    tags JSONB DEFAULT '[]'::jsonb, -- Tags for categorization
    word_count INTEGER, -- Number of words in content
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    -- Ensure either element_id or project_id is set, but not both
    CONSTRAINT documentation_scope_check CHECK (
        (element_id IS NOT NULL AND project_id IS NULL) OR
        (element_id IS NULL AND project_id IS NOT NULL)
    )
);

-- Document embeddings for semantic search
CREATE TABLE document_embeddings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    documentation_id UUID NOT NULL REFERENCES documentation(id) ON DELETE CASCADE,
    chunk_index INTEGER NOT NULL DEFAULT 0, -- For document chunking
    chunk_text TEXT NOT NULL,
    chunk_type VARCHAR(50) DEFAULT 'content', -- 'title', 'content', 'example', 'summary'
    embedding vector(1536) NOT NULL, -- OpenAI ada-002 dimensions (1536)
    embedding_model VARCHAR(100) NOT NULL DEFAULT 'text-embedding-ada-002',
    token_count INTEGER, -- Number of tokens in chunk
    char_count INTEGER, -- Number of characters in chunk
    metadata JSONB DEFAULT '{}'::jsonb, -- Chunk-specific metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(documentation_id, chunk_index)
);

-- Search and query logs for analytics
CREATE TABLE search_queries (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID REFERENCES projects(id) ON DELETE SET NULL,
    query_text TEXT NOT NULL,
    query_type VARCHAR(50) DEFAULT 'semantic', -- 'semantic', 'keyword', 'hybrid'
    query_embedding vector(1536), -- Embedding of the query
    results_found INTEGER NOT NULL DEFAULT 0,
    response_time_ms INTEGER, -- Query execution time
    user_agent VARCHAR(500), -- If from web interface
    ip_address INET, -- Client IP (if applicable)
    session_id VARCHAR(100), -- Session tracking
    feedback_score INTEGER, -- User feedback (1-5)
    feedback_text TEXT, -- User feedback comments
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Knowledge graph relationships (for advanced features)
CREATE TABLE code_relationships (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    source_element_id UUID NOT NULL REFERENCES code_elements(id) ON DELETE CASCADE,
    target_element_id UUID NOT NULL REFERENCES code_elements(id) ON DELETE CASCADE,
    relationship_type VARCHAR(50) NOT NULL, -- 'calls', 'inherits', 'imports', 'uses', 'implements'
    strength FLOAT DEFAULT 1.0, -- Relationship strength (0-1)
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(source_element_id, target_element_id, relationship_type)
);

-- ============================================================================
-- INDEXES FOR PERFORMANCE
-- ============================================================================

-- Primary lookup indexes
CREATE INDEX idx_code_files_project_id ON code_files(project_id);
CREATE INDEX idx_code_files_file_type ON code_files(file_type);
CREATE INDEX idx_code_files_last_analyzed ON code_files(last_analyzed);
CREATE INDEX idx_code_files_hash ON code_files(content_hash);

CREATE INDEX idx_code_elements_file_id ON code_elements(file_id);
CREATE INDEX idx_code_elements_type ON code_elements(element_type);
CREATE INDEX idx_code_elements_name ON code_elements(name);
CREATE INDEX idx_code_elements_full_name ON code_elements(full_name);

CREATE INDEX idx_documentation_element_id ON documentation(element_id);
CREATE INDEX idx_documentation_project_id ON documentation(project_id);
CREATE INDEX idx_documentation_type ON documentation(doc_type);
CREATE INDEX idx_documentation_quality ON documentation(quality_score);
CREATE INDEX idx_documentation_approved ON documentation(approved);

-- Vector similarity search indexes (HNSW for better performance)
CREATE INDEX idx_doc_embeddings_vector_hnsw ON document_embeddings
    USING hnsw (embedding vector_cosine_ops)
    WITH (m = 16, ef_construction = 64);

-- IVFFlat index as fallback (faster build time)
CREATE INDEX idx_doc_embeddings_vector_ivf ON document_embeddings
    USING ivfflat (embedding vector_cosine_ops)
    WITH (lists = 100);

-- Search query indexes
CREATE INDEX idx_search_queries_project_id ON search_queries(project_id);
CREATE INDEX idx_search_queries_created_at ON search_queries(created_at);
CREATE INDEX idx_search_queries_type ON search_queries(query_type);

-- Relationship indexes
CREATE INDEX idx_code_relationships_source ON code_relationships(source_element_id);
CREATE INDEX idx_code_relationships_target ON code_relationships(target_element_id);
CREATE INDEX idx_code_relationships_type ON code_relationships(relationship_type);

-- Composite indexes for common queries
CREATE INDEX idx_code_files_project_type ON code_files(project_id, file_type);
CREATE INDEX idx_code_elements_file_type ON code_elements(file_id, element_type);
CREATE INDEX idx_documentation_element_type ON documentation(element_id, doc_type);
CREATE INDEX idx_embeddings_doc_chunk ON document_embeddings(documentation_id, chunk_index);

-- ============================================================================
-- TRIGGERS FOR AUTOMATIC UPDATES
-- ============================================================================

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply triggers to tables with updated_at
CREATE TRIGGER update_projects_updated_at
    BEFORE UPDATE ON projects
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_code_files_updated_at
    BEFORE UPDATE ON code_files
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_documentation_updated_at
    BEFORE UPDATE ON documentation
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- VIEWS FOR COMMON QUERIES
-- ============================================================================

-- View for file analysis summary
CREATE VIEW file_analysis_summary AS
SELECT
    p.name as project_name,
    cf.file_path,
    cf.file_type,
    cf.line_count,
    COUNT(ce.id) as element_count,
    COUNT(DISTINCT ce.element_type) as element_types,
    cf.last_analyzed,
    cf.created_at
FROM projects p
JOIN code_files cf ON p.id = cf.project_id
LEFT JOIN code_elements ce ON cf.id = ce.file_id
GROUP BY p.id, p.name, cf.id, cf.file_path, cf.file_type, cf.line_count, cf.last_analyzed, cf.created_at;

-- View for documentation coverage
CREATE VIEW documentation_coverage AS
SELECT
    p.name as project_name,
    ce.element_type,
    COUNT(ce.id) as total_elements,
    COUNT(d.id) as documented_elements,
    ROUND(
        (COUNT(d.id)::float / NULLIF(COUNT(ce.id), 0)) * 100, 2
    ) as coverage_percentage
FROM projects p
JOIN code_files cf ON p.id = cf.project_id
JOIN code_elements ce ON cf.id = ce.file_id
LEFT JOIN documentation d ON ce.id = d.element_id AND d.approved = true
GROUP BY p.id, p.name, ce.element_type;

-- View for search analytics
CREATE VIEW search_analytics AS
SELECT
    p.name as project_name,
    sq.query_type,
    COUNT(*) as query_count,
    AVG(sq.results_found) as avg_results,
    AVG(sq.response_time_ms) as avg_response_time,
    AVG(sq.feedback_score) as avg_feedback_score,
    DATE_TRUNC('day', sq.created_at) as query_date
FROM search_queries sq
LEFT JOIN projects p ON sq.project_id = p.id
GROUP BY p.id, p.name, sq.query_type, DATE_TRUNC('day', sq.created_at);

-- ============================================================================
-- UTILITY FUNCTIONS
-- ============================================================================

-- Function to calculate documentation quality score
CREATE OR REPLACE FUNCTION calculate_doc_quality_score(
    completeness FLOAT,
    clarity FLOAT,
    accuracy FLOAT
) RETURNS FLOAT AS $$
BEGIN
    -- Weighted average: completeness 40%, clarity 30%, accuracy 30%
    RETURN (completeness * 0.4 + clarity * 0.3 + accuracy * 0.3);
END;
$$ LANGUAGE plpgsql;

-- Function to get similar documents using vector search
CREATE OR REPLACE FUNCTION find_similar_documents(
    query_embedding vector(1536),
    similarity_threshold FLOAT DEFAULT 0.7,
    max_results INTEGER DEFAULT 10
) RETURNS TABLE (
    doc_id UUID,
    chunk_text TEXT,
    similarity FLOAT
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        de.documentation_id,
        de.chunk_text,
        1 - (de.embedding <=> query_embedding) as similarity
    FROM document_embeddings de
    WHERE 1 - (de.embedding <=> query_embedding) > similarity_threshold
    ORDER BY de.embedding <=> query_embedding
    LIMIT max_results;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- SAMPLE DATA TYPES AND CONSTRAINTS
-- ============================================================================

-- Add check constraints for data validation
ALTER TABLE code_elements ADD CONSTRAINT valid_element_type
    CHECK (element_type IN ('function', 'class', 'method', 'variable', 'module', 'import', 'constant'));

ALTER TABLE documentation ADD CONSTRAINT valid_doc_type
    CHECK (doc_type IN ('api', 'tutorial', 'overview', 'example', 'troubleshooting', 'changelog', 'readme'));

ALTER TABLE documentation ADD CONSTRAINT valid_quality_scores
    CHECK (quality_score BETWEEN 0 AND 1 AND
           completeness_score BETWEEN 0 AND 1 AND
           clarity_score BETWEEN 0 AND 1 AND
           accuracy_score BETWEEN 0 AND 1);

ALTER TABLE code_relationships ADD CONSTRAINT valid_relationship_type
    CHECK (relationship_type IN ('calls', 'inherits', 'imports', 'uses', 'implements', 'contains', 'references'));

-- ============================================================================
-- COMMENTS FOR DOCUMENTATION
-- ============================================================================

COMMENT ON TABLE projects IS 'Root level organization for code repositories and documentation projects';
COMMENT ON TABLE code_files IS 'Individual source code files with content and metadata';
COMMENT ON TABLE code_elements IS 'Parsed code elements like functions, classes, methods extracted from files';
COMMENT ON TABLE documentation IS 'Generated documentation content for code elements or projects';
COMMENT ON TABLE document_embeddings IS 'Vector embeddings of documentation chunks for semantic search';
COMMENT ON TABLE search_queries IS 'Log of search queries for analytics and improvement';
COMMENT ON TABLE code_relationships IS 'Relationships between code elements for knowledge graph';

-- Schema version tracking
CREATE TABLE schema_version (
    version VARCHAR(20) PRIMARY KEY,
    applied_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    description TEXT
);

INSERT INTO schema_version (version, description)
VALUES ('1.0.0', 'Initial schema with pgvector support for code-to-documentation system');