-- Database schema for Engels system
-- PostgreSQL 15+ with pgvector extension

-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Sources: metadata for uploaded documents
CREATE TABLE sources (
    id SERIAL PRIMARY KEY,
    title VARCHAR(500) NOT NULL,
    file_path VARCHAR(1000),
    file_type VARCHAR(50),
    upload_status VARCHAR(50) DEFAULT 'pending',
    processing_status VARCHAR(50) DEFAULT 'pending',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB DEFAULT '{}'::jsonb
);

CREATE INDEX idx_sources_upload_status ON sources(upload_status);
CREATE INDEX idx_sources_processing_status ON sources(processing_status);

-- Text chunks: segmented text with embeddings
CREATE TABLE text_chunks (
    id SERIAL PRIMARY KEY,
    source_id INTEGER NOT NULL REFERENCES sources(id) ON DELETE CASCADE,
    chunk_index INTEGER NOT NULL,
    text TEXT NOT NULL,
    embedding vector(768),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(source_id, chunk_index)
);

CREATE INDEX idx_text_chunks_source_id ON text_chunks(source_id);
CREATE INDEX idx_text_chunks_embedding ON text_chunks USING hnsw (embedding vector_cosine_ops);

-- Entities: graph nodes (persons, events, concepts, etc.)
CREATE TABLE entities (
    id SERIAL PRIMARY KEY,
    name VARCHAR(500) NOT NULL,
    entity_type VARCHAR(100) NOT NULL,
    category VARCHAR(100),
    description TEXT,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_entities_name ON entities(name);
CREATE INDEX idx_entities_type ON entities(entity_type);
CREATE INDEX idx_entities_category ON entities(category);
CREATE INDEX idx_entities_metadata ON entities USING GIN (metadata);

-- Relations: graph edges with verification status
CREATE TABLE relations (
    id SERIAL PRIMARY KEY,
    subject_id INTEGER NOT NULL REFERENCES entities(id) ON DELETE CASCADE,
    object_id INTEGER NOT NULL REFERENCES entities(id) ON DELETE CASCADE,
    predicate VARCHAR(200) NOT NULL,
    confidence_score REAL DEFAULT 0.0,
    status VARCHAR(50) DEFAULT 'raw' CHECK (status IN ('raw', 'verified', 'rejected')),
    evidence_quote TEXT,
    source_mcp BOOLEAN DEFAULT FALSE,
    source_id INTEGER REFERENCES sources(id),
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    verified_by INTEGER,
    verified_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_relations_subject ON relations(subject_id);
CREATE INDEX idx_relations_object ON relations(object_id);
CREATE INDEX idx_relations_predicate ON relations(predicate);
CREATE INDEX idx_relations_status ON relations(status);
CREATE INDEX idx_relations_source_mcp ON relations(source_mcp);
CREATE INDEX idx_relations_metadata ON relations USING GIN (metadata);

-- Audit log for tracking changes
CREATE TABLE audit_log (
    id SERIAL PRIMARY KEY,
    table_name VARCHAR(100) NOT NULL,
    record_id INTEGER NOT NULL,
    action VARCHAR(50) NOT NULL,
    old_values JSONB,
    new_values JSONB,
    changed_by INTEGER,
    changed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_audit_log_table_record ON audit_log(table_name, record_id);
CREATE INDEX idx_audit_log_changed_at ON audit_log(changed_at);

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Triggers for updated_at
CREATE TRIGGER update_sources_updated_at
    BEFORE UPDATE ON sources
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_entities_updated_at
    BEFORE UPDATE ON entities
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_relations_updated_at
    BEFORE UPDATE ON relations
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();
