-- Document Intelligence Platform - Database Schema
-- PostgreSQL 15+
-- Sprint 1: Database & Data Models

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";  -- For fuzzy text search

-- ============================================================================
-- DOCUMENTS TABLE
-- ============================================================================
CREATE TABLE documents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- File Information
    filename VARCHAR(255) NOT NULL,
    original_path TEXT NOT NULL,
    file_type VARCHAR(50) NOT NULL,
    file_size BIGINT NOT NULL,
    mime_type VARCHAR(100),
    
    -- Timestamps
    upload_date TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_modified TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    processed_date TIMESTAMP WITH TIME ZONE,
    
    -- Content
    raw_text TEXT,
    page_count INTEGER,
    word_count INTEGER,
    
    -- AI-generated content (JSONB for flexibility)
    summary TEXT,
    key_points JSONB DEFAULT '[]'::jsonb,
    entities JSONB DEFAULT '{}'::jsonb,  -- {people: [], organizations: [], dates: [], locations: []}
    action_items JSONB DEFAULT '[]'::jsonb,
    
    -- Categorization
    ai_category_id UUID REFERENCES categories(id) ON DELETE SET NULL,
    ai_confidence FLOAT CHECK (ai_confidence >= 0 AND ai_confidence <= 1),
    user_category_id UUID REFERENCES categories(id) ON DELETE SET NULL,
    
    -- Tags (array for quick filtering)
    ai_tags TEXT[] DEFAULT '{}',
    user_tags TEXT[] DEFAULT '{}',
    
    -- Metadata from file
    extracted_metadata JSONB DEFAULT '{}'::jsonb,
    
    -- Processing status
    processing_status VARCHAR(50) DEFAULT 'pending' CHECK (
        processing_status IN ('pending', 'processing', 'completed', 'failed')
    ),
    processing_error TEXT,
    
    -- Source information
    source VARCHAR(50) NOT NULL CHECK (
        source IN ('upload', 'gmail', 'gdrive', 'dropbox', 'onedrive')
    ),
    source_id VARCHAR(255),  -- ID from source system (e.g., Gmail message ID)
    connection_id UUID REFERENCES connections(id) ON DELETE SET NULL,
    
    -- User flags
    is_favorite BOOLEAN DEFAULT FALSE,
    is_archived BOOLEAN DEFAULT FALSE,
    user_notes TEXT,
    
    -- Full-text search vector
    search_vector tsvector,
    
    -- Audit
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for documents table
CREATE INDEX idx_documents_upload_date ON documents(upload_date DESC);
CREATE INDEX idx_documents_processing_status ON documents(processing_status);
CREATE INDEX idx_documents_ai_category ON documents(ai_category_id);
CREATE INDEX idx_documents_user_category ON documents(user_category_id);
CREATE INDEX idx_documents_source ON documents(source);
CREATE INDEX idx_documents_connection ON documents(connection_id);
CREATE INDEX idx_documents_favorite ON documents(is_favorite) WHERE is_favorite = TRUE;
CREATE INDEX idx_documents_archived ON documents(is_archived) WHERE is_archived = TRUE;
CREATE INDEX idx_documents_tags ON documents USING GIN(ai_tags);
CREATE INDEX idx_documents_user_tags ON documents USING GIN(user_tags);
CREATE INDEX idx_documents_search ON documents USING GIN(search_vector);
CREATE INDEX idx_documents_entities ON documents USING GIN(entities);

-- ============================================================================
-- CATEGORIES TABLE
-- ============================================================================
CREATE TABLE categories (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Basic info
    name VARCHAR(100) UNIQUE NOT NULL,
    slug VARCHAR(100) UNIQUE NOT NULL,
    description TEXT,
    
    -- Visual
    color VARCHAR(7) DEFAULT '#3B82F6',  -- Hex color
    icon VARCHAR(50),  -- Icon name/emoji
    
    -- Origin
    ai_generated BOOLEAN DEFAULT TRUE,
    created_by_user BOOLEAN DEFAULT FALSE,
    
    -- Stats
    document_count INTEGER DEFAULT 0,
    last_used TIMESTAMP WITH TIME ZONE,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for categories
CREATE INDEX idx_categories_name ON categories(name);
CREATE INDEX idx_categories_slug ON categories(slug);
CREATE INDEX idx_categories_ai_generated ON categories(ai_generated);
CREATE INDEX idx_categories_document_count ON categories(document_count DESC);

-- ============================================================================
-- DOCUMENT RELATIONSHIPS TABLE
-- ============================================================================
CREATE TABLE document_relationships (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    source_doc_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    target_doc_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    
    relationship_type VARCHAR(50) NOT NULL CHECK (
        relationship_type IN ('similar_to', 'references', 'follows_up', 'related_to', 'duplicates')
    ),
    
    confidence FLOAT CHECK (confidence >= 0 AND confidence <= 1),
    
    -- Metadata about the relationship
    metadata JSONB DEFAULT '{}'::jsonb,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Prevent self-references
    CONSTRAINT no_self_reference CHECK (source_doc_id != target_doc_id),
    
    -- Prevent duplicate relationships
    CONSTRAINT unique_relationship UNIQUE (source_doc_id, target_doc_id, relationship_type)
);

-- Indexes for relationships
CREATE INDEX idx_relationships_source ON document_relationships(source_doc_id);
CREATE INDEX idx_relationships_target ON document_relationships(target_doc_id);
CREATE INDEX idx_relationships_type ON document_relationships(relationship_type);
CREATE INDEX idx_relationships_confidence ON document_relationships(confidence DESC);

-- ============================================================================
-- CONNECTIONS TABLE (Cloud Services)
-- ============================================================================
CREATE TABLE connections (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Connection type
    type VARCHAR(50) NOT NULL CHECK (
        type IN ('gmail', 'gdrive', 'dropbox', 'onedrive')
    ),
    
    status VARCHAR(50) DEFAULT 'disconnected' CHECK (
        status IN ('connected', 'disconnected', 'error', 'syncing')
    ),
    
    -- Display information
    display_name VARCHAR(255) NOT NULL,
    email VARCHAR(255),
    
    -- Sync information
    last_sync_date TIMESTAMP WITH TIME ZONE,
    last_sync_status VARCHAR(50) CHECK (
        last_sync_status IN ('success', 'failed', 'partial', 'in_progress')
    ),
    sync_progress INTEGER DEFAULT 0 CHECK (sync_progress >= 0 AND sync_progress <= 100),
    
    -- Stats
    document_count INTEGER DEFAULT 0,
    total_size BIGINT DEFAULT 0,  -- bytes
    
    -- Settings
    auto_sync BOOLEAN DEFAULT TRUE,
    sync_interval INTEGER DEFAULT 15,  -- minutes
    
    -- Authentication (tokens stored encrypted elsewhere)
    is_authenticated BOOLEAN DEFAULT FALSE,
    token_expires_at TIMESTAMP WITH TIME ZONE,
    
    -- Sync state (last cursor/token for incremental sync)
    sync_state JSONB DEFAULT '{}'::jsonb,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- One connection per type per user
    CONSTRAINT unique_connection_type UNIQUE (type)
);

-- Indexes for connections
CREATE INDEX idx_connections_type ON connections(type);
CREATE INDEX idx_connections_status ON connections(status);
CREATE INDEX idx_connections_last_sync ON connections(last_sync_date DESC);

-- ============================================================================
-- SYNC LOGS TABLE
-- ============================================================================
CREATE TABLE sync_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    connection_id UUID NOT NULL REFERENCES connections(id) ON DELETE CASCADE,
    
    start_time TIMESTAMP WITH TIME ZONE NOT NULL,
    end_time TIMESTAMP WITH TIME ZONE,
    
    status VARCHAR(50) DEFAULT 'in_progress' CHECK (
        status IN ('success', 'failed', 'partial', 'in_progress')
    ),
    
    -- Statistics
    documents_added INTEGER DEFAULT 0,
    documents_updated INTEGER DEFAULT 0,
    documents_failed INTEGER DEFAULT 0,
    bytes_synced BIGINT DEFAULT 0,
    
    -- Error information
    error_message TEXT,
    error_details JSONB,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for sync logs
CREATE INDEX idx_sync_logs_connection ON sync_logs(connection_id);
CREATE INDEX idx_sync_logs_start_time ON sync_logs(start_time DESC);
CREATE INDEX idx_sync_logs_status ON sync_logs(status);

-- ============================================================================
-- PROCESSING QUEUE TABLE
-- ============================================================================
CREATE TABLE processing_queue (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    
    task_type VARCHAR(50) NOT NULL CHECK (
        task_type IN ('extract_text', 'ai_analysis', 'generate_thumbnail', 'embed_document', 'detect_relationships')
    ),
    
    status VARCHAR(50) DEFAULT 'queued' CHECK (
        status IN ('queued', 'processing', 'completed', 'failed')
    ),
    
    priority INTEGER DEFAULT 5 CHECK (priority >= 1 AND priority <= 10),
    
    -- Retry logic
    attempts INTEGER DEFAULT 0,
    max_attempts INTEGER DEFAULT 3,
    
    -- Error tracking
    error_message TEXT,
    error_details JSONB,
    
    -- Timing
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    
    -- Prevent duplicate tasks
    CONSTRAINT unique_document_task UNIQUE (document_id, task_type)
);

-- Indexes for processing queue
CREATE INDEX idx_queue_status ON processing_queue(status);
CREATE INDEX idx_queue_priority ON processing_queue(priority DESC, created_at ASC);
CREATE INDEX idx_queue_document ON processing_queue(document_id);
CREATE INDEX idx_queue_task_type ON processing_queue(task_type);

-- ============================================================================
-- DOCUMENT VERSIONS TABLE (for tracking changes from cloud sources)
-- ============================================================================
CREATE TABLE document_versions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    
    version_number INTEGER NOT NULL,
    
    -- What changed
    changed_fields JSONB DEFAULT '[]'::jsonb,
    
    -- Snapshot of document at this version
    snapshot JSONB NOT NULL,
    
    -- Who/what made the change
    changed_by VARCHAR(50) CHECK (
        changed_by IN ('user', 'ai', 'sync')
    ),
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    CONSTRAINT unique_document_version UNIQUE (document_id, version_number)
);

-- Indexes for versions
CREATE INDEX idx_versions_document ON document_versions(document_id);
CREATE INDEX idx_versions_created ON document_versions(created_at DESC);

-- ============================================================================
-- TRIGGERS
-- ============================================================================

-- Auto-update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_documents_updated_at BEFORE UPDATE ON documents
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_categories_updated_at BEFORE UPDATE ON categories
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_connections_updated_at BEFORE UPDATE ON connections
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Auto-update search vector
CREATE OR REPLACE FUNCTION update_search_vector()
RETURNS TRIGGER AS $$
BEGIN
    NEW.search_vector := 
        setweight(to_tsvector('english', COALESCE(NEW.filename, '')), 'A') ||
        setweight(to_tsvector('english', COALESCE(NEW.summary, '')), 'B') ||
        setweight(to_tsvector('english', COALESCE(NEW.raw_text, '')), 'C');
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER documents_search_vector_update 
    BEFORE INSERT OR UPDATE ON documents
    FOR EACH ROW EXECUTE FUNCTION update_search_vector();

-- Update category document count
CREATE OR REPLACE FUNCTION update_category_count()
RETURNS TRIGGER AS $$
BEGIN
    -- Decrement old category
    IF OLD.ai_category_id IS NOT NULL THEN
        UPDATE categories 
        SET document_count = document_count - 1
        WHERE id = OLD.ai_category_id;
    END IF;
    
    -- Increment new category
    IF NEW.ai_category_id IS NOT NULL THEN
        UPDATE categories 
        SET document_count = document_count + 1,
            last_used = NOW()
        WHERE id = NEW.ai_category_id;
    END IF;
    
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_category_document_count
    AFTER INSERT OR UPDATE OF ai_category_id ON documents
    FOR EACH ROW EXECUTE FUNCTION update_category_count();

-- ============================================================================
-- INITIAL DATA SEEDING
-- ============================================================================

-- Insert default categories (will be replaced by AI-discovered ones)
INSERT INTO categories (name, slug, description, color, icon, ai_generated, created_by_user) VALUES
    ('Uncategorized', 'uncategorized', 'Documents not yet categorized', '#6B7280', '📄', FALSE, FALSE),
    ('Work', 'work', 'Work-related documents', '#3B82F6', '💼', TRUE, FALSE),
    ('Personal', 'personal', 'Personal documents', '#10B981', '👤', TRUE, FALSE),
    ('Finance', 'finance', 'Financial documents', '#F59E0B', '💰', TRUE, FALSE),
    ('Health', 'health', 'Health and medical documents', '#8B5CF6', '🏥', TRUE, FALSE),
    ('Legal', 'legal', 'Legal documents', '#EF4444', '⚖️', TRUE, FALSE),
    ('Travel', 'travel', 'Travel-related documents', '#F97316', '✈️', TRUE, FALSE),
    ('Education', 'education', 'Educational documents', '#06B6D4', '🎓', TRUE, FALSE);

-- ============================================================================
-- VIEWS FOR COMMON QUERIES
-- ============================================================================

-- Recent documents with category info
CREATE VIEW recent_documents_view AS
SELECT 
    d.id,
    d.filename,
    d.file_type,
    d.file_size,
    d.upload_date,
    d.summary,
    d.processing_status,
    d.source,
    d.is_favorite,
    c.name as category_name,
    c.color as category_color,
    c.icon as category_icon,
    array_length(d.ai_tags, 1) as tag_count
FROM documents d
LEFT JOIN categories c ON d.ai_category_id = c.id
WHERE d.is_archived = FALSE
ORDER BY d.upload_date DESC;

-- Category statistics
CREATE VIEW category_stats_view AS
SELECT 
    c.id,
    c.name,
    c.color,
    c.icon,
    c.document_count,
    COUNT(d.id) as actual_count,
    SUM(d.file_size) as total_size,
    MAX(d.upload_date) as latest_document,
    c.last_used
FROM categories c
LEFT JOIN documents d ON d.ai_category_id = c.id
GROUP BY c.id, c.name, c.color, c.icon, c.document_count, c.last_used;

-- Connection status overview
CREATE VIEW connection_status_view AS
SELECT 
    c.id,
    c.type,
    c.status,
    c.display_name,
    c.document_count,
    c.last_sync_date,
    c.last_sync_status,
    c.is_authenticated,
    CASE 
        WHEN c.last_sync_date IS NULL THEN 'Never synced'
        WHEN c.last_sync_date < NOW() - INTERVAL '1 hour' THEN 'Outdated'
        ELSE 'Recent'
    END as sync_freshness
FROM connections c;

-- ============================================================================
-- FUNCTIONS FOR COMMON OPERATIONS
-- ============================================================================

-- Search documents by text
CREATE OR REPLACE FUNCTION search_documents(query_text TEXT)
RETURNS TABLE (
    document_id UUID,
    filename VARCHAR,
    summary TEXT,
    relevance REAL
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        d.id,
        d.filename,
        d.summary,
        ts_rank(d.search_vector, plainto_tsquery('english', query_text)) as relevance
    FROM documents d
    WHERE d.search_vector @@ plainto_tsquery('english', query_text)
        AND d.is_archived = FALSE
    ORDER BY relevance DESC;
END;
$$ LANGUAGE plpgsql;

-- Get document timeline
CREATE OR REPLACE FUNCTION get_document_timeline(
    start_date DATE DEFAULT NULL,
    end_date DATE DEFAULT NULL,
    limit_count INTEGER DEFAULT 50,
    offset_count INTEGER DEFAULT 0
)
RETURNS TABLE (
    document_id UUID,
    filename VARCHAR,
    upload_date TIMESTAMP WITH TIME ZONE,
    category_name VARCHAR,
    summary TEXT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        d.id,
        d.filename,
        d.upload_date,
        c.name,
        d.summary
    FROM documents d
    LEFT JOIN categories c ON d.ai_category_id = c.id
    WHERE 
        (start_date IS NULL OR d.upload_date >= start_date)
        AND (end_date IS NULL OR d.upload_date <= end_date)
        AND d.is_archived = FALSE
    ORDER BY d.upload_date DESC
    LIMIT limit_count
    OFFSET offset_count;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- PERFORMANCE MONITORING
-- ============================================================================

-- Create statistics for query optimization
ANALYZE documents;
ANALYZE categories;
ANALYZE document_relationships;
ANALYZE connections;

-- ============================================================================
-- COMMENTS FOR DOCUMENTATION
-- ============================================================================

COMMENT ON TABLE documents IS 'Core table storing all documents from various sources';
COMMENT ON TABLE categories IS 'AI-discovered and user-created categories for document organization';
COMMENT ON TABLE document_relationships IS 'Links between related documents';
COMMENT ON TABLE connections IS 'Cloud service connections (Gmail, Drive, Dropbox, etc.)';
COMMENT ON TABLE sync_logs IS 'Audit log of synchronization activities';
COMMENT ON TABLE processing_queue IS 'Queue for background document processing tasks';
COMMENT ON TABLE document_versions IS 'Version history for documents';

COMMENT ON COLUMN documents.search_vector IS 'Full-text search index combining filename, summary, and content';
COMMENT ON COLUMN documents.entities IS 'JSONB object with extracted entities: {people: [], organizations: [], dates: [], locations: []}';
COMMENT ON COLUMN documents.key_points IS 'JSONB array of important points extracted from document';
COMMENT ON COLUMN documents.action_items IS 'JSONB array of action items found in document';
