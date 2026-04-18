from datetime import datetime

from pydantic import BaseModel, Field


class EntityBase(BaseModel):
    """Base schema for entities (graph nodes)."""

    name: str
    entity_type: str
    category: str | None = None
    description: str | None = None
    metadata: dict = Field(default_factory=dict)


class EntityCreate(EntityBase):
    """Schema for creating a new entity."""

    pass


class Entity(EntityBase):
    """Schema for an entity with database fields."""

    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class RelationBase(BaseModel):
    """Base schema for relations (graph edges)."""

    subject_id: int
    object_id: int
    predicate: str
    confidence_score: float = 0.0
    evidence_quote: str | None = None
    source_mcp: bool = False
    source_id: int | None = None
    metadata: dict = Field(default_factory=dict)


class RelationCreate(RelationBase):
    """Schema for creating a new relation."""

    pass


class Relation(RelationBase):
    """Schema for a relation with database fields."""

    id: int
    status: str  # raw, verified, rejected
    created_at: datetime
    updated_at: datetime
    verified_by: int | None = None
    verified_at: datetime | None = None

    class Config:
        from_attributes = True


class SourceBase(BaseModel):
    """Base schema for document sources."""

    title: str
    file_path: str | None = None
    file_type: str | None = None
    metadata: dict = Field(default_factory=dict)


class SourceCreate(SourceBase):
    """Schema for creating a new source."""

    pass


class Source(SourceBase):
    """Schema for a source with database fields."""

    id: int
    upload_status: str
    processing_status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TextChunkBase(BaseModel):
    """Base schema for text chunks."""

    source_id: int
    chunk_index: int
    text: str


class TextChunkCreate(TextChunkBase):
    """Schema for creating a text chunk."""

    embedding: list[float] | None = None


class TextChunk(TextChunkBase):
    """Schema for a text chunk with database fields."""

    id: int
    created_at: datetime
    embedding: list[float] | None = None

    class Config:
        from_attributes = True


class ExtractionResult(BaseModel):
    """Schema for LLM extraction results."""

    entities: list[EntityCreate]
    relations: list[RelationCreate]
    confidence_score: float = 0.0


class MCPRequest(BaseModel):
    """Schema for MCP external processing request."""

    task_type: str
    anonymized_context: str
    token_map_id: str  # Reference to in-memory token mapping


class MCPResponse(BaseModel):
    """Schema for MCP external processing response."""

    result: ExtractionResult
    success: bool
    error_message: str | None = None


class QueryRequest(BaseModel):
    """Schema for RAG query request."""

    question: str
    source_id: int | None = None
    include_sources: bool = True
    top_k: int = 5


class QueryResponse(BaseModel):
    """Schema for RAG query response."""

    answer: str
    context: str
    sources: list[dict] = []
    chunks_used: int = 0
    metadata: dict = Field(default_factory=dict)


class HealthResponse(BaseModel):
    """Schema for health check response."""

    status: str
    components: dict
    timestamp: datetime
