from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class EntityBase(BaseModel):
    """Base schema for entities (graph nodes)."""
    name: str
    entity_type: str
    category: Optional[str] = None
    description: Optional[str] = None
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
    evidence_quote: Optional[str] = None
    source_mcp: bool = False
    source_id: Optional[int] = None
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
    verified_by: Optional[int] = None
    verified_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class SourceBase(BaseModel):
    """Base schema for document sources."""
    title: str
    file_path: Optional[str] = None
    file_type: Optional[str] = None
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
    embedding: Optional[List[float]] = None


class TextChunk(TextChunkBase):
    """Schema for a text chunk with database fields."""
    id: int
    created_at: datetime
    embedding: Optional[List[float]] = None

    class Config:
        from_attributes = True


class ExtractionResult(BaseModel):
    """Schema for LLM extraction results."""
    entities: List[EntityCreate]
    relations: List[RelationCreate]
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
    error_message: Optional[str] = None
