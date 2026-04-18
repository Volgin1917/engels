"""
SQLAlchemy models for Engels project.
Defines database tables for sources, text chunks, entities, and relations.
"""

from datetime import datetime
from typing import Optional

from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, declarative_base, mapped_column, relationship
from sqlalchemy.sql import func

Base = declarative_base()


class Source(Base):
    """Document source table."""

    __tablename__ = "sources"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    file_path: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    file_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    extra_metadata: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)

    upload_status: Mapped[str] = mapped_column(
        String(50), default="uploaded", nullable=False
    )  # uploaded, processing, completed, failed
    processing_status: Mapped[str] = mapped_column(
        String(50), default="pending", nullable=False
    )  # pending, chunking, embedding, extracting, completed, failed

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    text_chunks: Mapped[list["TextChunk"]] = relationship(
        "TextChunk", back_populates="source", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("ix_sources_upload_status", "upload_status"),
        Index("ix_sources_processing_status", "processing_status"),
        Index("ix_sources_created_at", "created_at"),
    )


class TextChunk(Base):
    """Text chunk table with vector embeddings."""

    __tablename__ = "text_chunks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    source_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("sources.id", ondelete="CASCADE"), nullable=False, index=True
    )
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    embedding: Mapped[list[float] | None] = mapped_column(
        Vector(dim=768), nullable=True
    )  # Dimension depends on embedding model

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    source: Mapped["Source"] = relationship("Source", back_populates="text_chunks")

    __table_args__ = (
        Index("ix_text_chunks_source_id", "source_id"),
        Index("ix_text_chunks_chunk_index", "chunk_index"),
        # HNSW index for vector similarity search (created via SQL migration)
    )


class Entity(Base):
    """Extracted entity table (graph nodes)."""

    __tablename__ = "entities"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(500), nullable=False, index=True)
    entity_type: Mapped[str] = mapped_column(String(200), nullable=False)
    category: Mapped[str | None] = mapped_column(String(200), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    extra_metadata: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)

    needs_review: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    review_comment: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    outgoing_relations: Mapped[list["Relation"]] = relationship(
        "Relation",
        foreign_keys="Relation.subject_id",
        back_populates="subject",
        cascade="all, delete-orphan",
    )
    incoming_relations: Mapped[list["Relation"]] = relationship(
        "Relation", foreign_keys="Relation.object_id", back_populates="object"
    )

    __table_args__ = (
        Index("ix_entities_entity_type", "entity_type"),
        Index("ix_entities_category", "category"),
        Index("ix_entities_needs_review", "needs_review"),
    )


class Relation(Base):
    """Extracted relation table (graph edges)."""

    __tablename__ = "relations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    subject_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("entities.id", ondelete="CASCADE"), nullable=False, index=True
    )
    object_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("entities.id", ondelete="CASCADE"), nullable=False, index=True
    )
    predicate: Mapped[str] = mapped_column(String(200), nullable=False)
    confidence_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    evidence_quote: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_mcp: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    source_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("sources.id", ondelete="SET NULL"), nullable=True
    )
    extra_metadata: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)

    status: Mapped[str] = mapped_column(
        String(50), default="raw", nullable=False
    )  # raw, verified, rejected
    verified_by: Mapped[int | None] = mapped_column(Integer, nullable=True)
    verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    subject: Mapped["Entity"] = relationship(
        "Entity", foreign_keys=[subject_id], back_populates="outgoing_relations"
    )
    object: Mapped["Entity"] = relationship(
        "Entity", foreign_keys=[object_id], back_populates="incoming_relations"
    )
    source: Mapped[Optional["Source"]] = relationship("Source", back_populates="relations")

    __table_args__ = (
        Index("ix_relations_predicate", "predicate"),
        Index("ix_relations_status", "status"),
        Index("ix_relations_confidence", "confidence_score"),
        Index("ix_relations_subject_object", "subject_id", "object_id"),
    )


class AuditLog(Base):
    """Audit log table for tracking changes."""

    __tablename__ = "audit_log"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    table_name: Mapped[str] = mapped_column(String(100), nullable=False)
    record_id: Mapped[int] = mapped_column(Integer, nullable=False)
    action: Mapped[str] = mapped_column(String(50), nullable=False)  # INSERT, UPDATE, DELETE
    old_values: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    new_values: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    changed_by: Mapped[int | None] = mapped_column(Integer, nullable=True)  # User ID
    changed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    __table_args__ = (
        Index("ix_audit_log_table_name", "table_name"),
        Index("ix_audit_log_record_id", "record_id"),
        Index("ix_audit_log_changed_at", "changed_at"),
    )


# Add relationship to Source for relations
Source.relations = relationship("Relation", back_populates="source")
