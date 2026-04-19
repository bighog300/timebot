-- Document Intelligence Platform - Database Schema
-- PostgreSQL 15+
-- NOTE: SQLAlchemy's init_db() is the recommended way to create tables.
-- Use this file for reference or direct psql initialisation.

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- ============================================================================
-- CATEGORIES (must come before documents due to FK references)
-- ============================================================================
CREATE TABLE IF NOT EXISTS categories (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) UNIQUE NOT NULL,
    slug VARCHAR(100) UNIQUE NOT NULL,
    description TEXT,
    color VARCHAR(7) DEFAULT '#3B82F6',
    icon VARCHAR(50),
    ai_generated BOOLEAN DEFAULT TRUE,
    created_by_user BOOLEAN DEFAULT FALSE,
    document_count INTEGER DEFAULT 0,
    last_used TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_categories_name ON categories(name);
CREATE INDEX IF NOT EXISTS idx_categories_slug ON categories(slug);
CREATE INDEX IF NOT EXISTS idx_categories_document_count ON categories(document_count DESC);

-- ============================================================================
-- CONNECTIONS (must come before documents due to FK references)
-- ============================================================================
CREATE TABLE IF NOT EXISTS connections (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    type VARCHAR(50) NOT NULL CHECK (type IN ('gmail', 'gdrive', 'dropbox', 'onedrive')),
    status VARCHAR(50) DEFAULT 'disconnected' CHECK (status IN ('connected', 'disconnected', 'error', 'syncing')),
    display_name VARCHAR(255) NOT NULL,
    email VARCHAR(255),
    last_sync_date TIMESTAMP WITH TIME ZONE,
    last_sync_status VARCHAR(50) CHECK (last_sync_status IS NULL OR last_sync_status IN ('success', 'failed', 'partial', 'in_progress')),
    sync_progress INTEGER DEFAULT 0 CHECK (sync_progress >= 0 AND sync_progress <= 100),
    document_count INTEGER DEFAULT 0,
    total_size BIGINT DEFAULT 0,
    auto_sync BOOLEAN DEFAULT TRUE,
    sync_interval INTEGER DEFAULT 15,
    is_authenticated BOOLEAN DEFAULT FALSE,
    token_expires_at TIMESTAMP WITH TIME ZONE,
    sync_state JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    CONSTRAINT unique_connection_type UNIQUE (type)
);

CREATE INDEX IF NOT EXISTS idx_connections_type ON connections(type);
CREATE INDEX IF NOT EXISTS idx_connections_status ON connections(status);

-- ============================================================================
-- DOCUMENTS
-- ============================================================================
CREATE TABLE IF NOT EXISTS documents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    filename VARCHAR(255) NOT NULL,
    original_path TEXT NOT NULL,
    file_type VARCHAR(50) NOT NULL,
    file_size BIGINT NOT NULL,
    mime_type VARCHAR(100),
    upload_date TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_modified TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    processed_date TIMESTAMP WITH TIME ZONE,
    raw_text TEXT,
    page_count INTEGER,
    word_count INTEGER,
    summary TEXT,
    key_points JSONB DEFAULT '[]'::jsonb,
    entities JSONB DEFAULT '{}'::jsonb,
    action_items JSONB DEFAULT '[]'::jsonb,
    ai_category_id UUID REFERENCES categories(id) ON DELETE SET NULL,
    ai_confidence FLOAT CHECK (ai_confidence IS NULL OR (ai_confidence >= 0 AND ai_confidence <= 1)),
    user_category_id UUID REFERENCES categories(id) ON DELETE SET NULL,
    ai_tags TEXT[] DEFAULT '{}',
    user_tags TEXT[] DEFAULT '{}',
    extracted_metadata JSONB DEFAULT '{}'::jsonb,
    processing_status VARCHAR(50) DEFAULT 'pending' CHECK (
        processing_status IN ('pending', 'queued', 'processing', 'completed', 'failed')
    ),
    processing_error TEXT,
    source VARCHAR(50) NOT NULL CHECK (
        source IN ('upload', 'gmail', 'gdrive', 'dropbox', 'onedrive')
    ),
    source_id VARCHAR(255),
    connection_id UUID REFERENCES connections(id) ON DELETE SET NULL,
    is_favorite BOOLEAN DEFAULT FALSE,
    is_archived BOOLEAN DEFAULT FALSE,
    user_notes TEXT,
    search_vector tsvector,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_documents_upload_date ON documents(upload_date DESC);
CREATE INDEX IF NOT EXISTS idx_documents_processing_status ON documents(processing_status);
CREATE INDEX IF NOT EXISTS idx_documents_ai_category ON documents(ai_category_id);
CREATE INDEX IF NOT EXISTS idx_documents_user_category ON documents(user_category_id);
CREATE INDEX IF NOT EXISTS idx_documents_source ON documents(source);
CREATE INDEX IF NOT EXISTS idx_documents_search ON documents USING GIN(search_vector);
CREATE INDEX IF NOT EXISTS idx_documents_tags ON documents USING GIN(ai_tags);
CREATE INDEX IF NOT EXISTS idx_documents_entities ON documents USING GIN(entities);

-- ============================================================================
-- DOCUMENT RELATIONSHIPS
-- ============================================================================
CREATE TABLE IF NOT EXISTS document_relationships (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    source_doc_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    target_doc_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    relationship_type VARCHAR(50) NOT NULL CHECK (
        relationship_type IN ('similar_to', 'references', 'follows_up', 'related_to', 'duplicates')
    ),
    confidence FLOAT CHECK (confidence IS NULL OR (confidence >= 0 AND confidence <= 1)),
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    CONSTRAINT no_self_reference CHECK (source_doc_id != target_doc_id),
    CONSTRAINT unique_relationship UNIQUE (source_doc_id, target_doc_id, relationship_type)
);

-- ============================================================================
-- SYNC LOGS
-- ============================================================================
CREATE TABLE IF NOT EXISTS sync_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    connection_id UUID NOT NULL REFERENCES connections(id) ON DELETE CASCADE,
    start_time TIMESTAMP WITH TIME ZONE NOT NULL,
    end_time TIMESTAMP WITH TIME ZONE,
    status VARCHAR(50) DEFAULT 'in_progress' CHECK (
        status IN ('success', 'failed', 'partial', 'in_progress')
    ),
    documents_added INTEGER DEFAULT 0,
    documents_updated INTEGER DEFAULT 0,
    documents_failed INTEGER DEFAULT 0,
    bytes_synced BIGINT DEFAULT 0,
    error_message TEXT,
    error_details JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ============================================================================
-- PROCESSING QUEUE
-- ============================================================================
CREATE TABLE IF NOT EXISTS processing_queue (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    task_type VARCHAR(50) NOT NULL CHECK (
        task_type IN ('extract_text', 'ai_analysis', 'generate_thumbnail', 'embed_document', 'detect_relationships')
    ),
    status VARCHAR(50) DEFAULT 'queued' CHECK (
        status IN ('queued', 'processing', 'completed', 'failed')
    ),
    priority INTEGER DEFAULT 5 CHECK (priority >= 1 AND priority <= 10),
    attempts INTEGER DEFAULT 0,
    max_attempts INTEGER DEFAULT 3,
    error_message TEXT,
    error_details JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    CONSTRAINT unique_document_task UNIQUE (document_id, task_type)
);

-- ============================================================================
-- DOCUMENT VERSIONS
-- ============================================================================
CREATE TABLE IF NOT EXISTS document_versions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    version_number INTEGER NOT NULL,
    changed_fields JSONB DEFAULT '[]'::jsonb,
    snapshot JSONB NOT NULL,
    changed_by VARCHAR(50) CHECK (changed_by IS NULL OR changed_by IN ('user', 'ai', 'sync')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    CONSTRAINT unique_document_version UNIQUE (document_id, version_number)
);

-- ============================================================================
-- TRIGGERS
-- ============================================================================
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN NEW.updated_at = NOW(); RETURN NEW; END;
$$ LANGUAGE plpgsql;

DO $$ BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'update_documents_updated_at') THEN
        CREATE TRIGGER update_documents_updated_at BEFORE UPDATE ON documents
            FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'update_categories_updated_at') THEN
        CREATE TRIGGER update_categories_updated_at BEFORE UPDATE ON categories
            FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
    END IF;
END $$;

CREATE OR REPLACE FUNCTION update_search_vector()
RETURNS TRIGGER AS $$
BEGIN
    NEW.search_vector :=
        setweight(to_tsvector('english', COALESCE(NEW.filename, '')), 'A') ||
        setweight(to_tsvector('english', COALESCE(NEW.summary, '')), 'B') ||
        setweight(to_tsvector('english', COALESCE(NEW.raw_text, '')), 'C');
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DO $$ BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'documents_search_vector_update') THEN
        CREATE TRIGGER documents_search_vector_update
            BEFORE INSERT OR UPDATE ON documents
            FOR EACH ROW EXECUTE FUNCTION update_search_vector();
    END IF;
END $$;

-- ============================================================================
-- DEFAULT SEED DATA
-- ============================================================================
INSERT INTO categories (name, slug, description, color, icon, ai_generated, created_by_user)
VALUES
    ('Uncategorized', 'uncategorized', 'Documents not yet categorized', '#6B7280', '📄', FALSE, FALSE),
    ('Work', 'work', 'Work-related documents', '#3B82F6', '💼', TRUE, FALSE),
    ('Personal', 'personal', 'Personal documents', '#10B981', '👤', TRUE, FALSE),
    ('Finance', 'finance', 'Financial documents', '#F59E0B', '💰', TRUE, FALSE),
    ('Health', 'health', 'Health and medical documents', '#8B5CF6', '🏥', TRUE, FALSE),
    ('Legal', 'legal', 'Legal documents', '#EF4444', '⚖️', TRUE, FALSE),
    ('Travel', 'travel', 'Travel-related documents', '#F97316', '✈️', TRUE, FALSE),
    ('Education', 'education', 'Educational documents', '#06B6D4', '🎓', TRUE, FALSE)
ON CONFLICT (name) DO NOTHING;
