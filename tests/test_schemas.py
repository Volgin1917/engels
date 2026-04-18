"""
Tests for Pydantic schemas.
"""
import pytest
from datetime import datetime

from backend.src.schemas import (
    EntityCreate, Entity, RelationCreate, Relation,
    SourceCreate, Source, ExtractionResult
)


class TestEntitySchemas:
    """Test entity validation schemas."""

    def test_entity_create_valid(self):
        """Test valid entity creation."""
        entity = EntityCreate(
            name="Karl Marx",
            entity_type="person",
            category="base",
            description="German philosopher"
        )
        assert entity.name == "Karl Marx"
        assert entity.entity_type == "person"
        assert entity.category == "base"

    def test_entity_create_minimal(self):
        """Test entity with minimal required fields."""
        entity = EntityCreate(
            name="Historical Event",
            entity_type="event"
        )
        assert entity.name == "Historical Event"
        assert entity.entity_type == "event"
        assert entity.category is None
        assert entity.metadata == {}

    def test_entity_with_metadata(self):
        """Test entity with custom metadata."""
        entity = EntityCreate(
            name="Concept",
            entity_type="concept",
            metadata={"era": "19th century", "region": "Europe"}
        )
        assert entity.metadata["era"] == "19th century"


class TestRelationSchemas:
    """Test relation validation schemas."""

    def test_relation_create_valid(self):
        """Test valid relation creation."""
        relation = RelationCreate(
            subject_id=1,
            object_id=2,
            predicate="influences",
            confidence_score=0.85,
            evidence_quote="Direct quote from source"
        )
        assert relation.subject_id == 1
        assert relation.object_id == 2
        assert relation.predicate == "influences"
        assert relation.confidence_score == 0.85

    def test_relation_mcp_flag(self):
        """Test MCP source flag."""
        relation = RelationCreate(
            subject_id=1,
            object_id=2,
            predicate="caused_by",
            source_mcp=True
        )
        assert relation.source_mcp is True

    def test_relation_default_values(self):
        """Test relation default values."""
        relation = RelationCreate(
            subject_id=1,
            object_id=2,
            predicate="part_of"
        )
        assert relation.confidence_score == 0.0
        assert relation.source_mcp is False
        assert relation.evidence_quote is None


class TestExtractionResult:
    """Test extraction result schema."""

    def test_extraction_result_empty(self):
        """Test empty extraction result."""
        result = ExtractionResult(
            entities=[],
            relations=[]
        )
        assert len(result.entities) == 0
        assert len(result.relations) == 0
        assert result.confidence_score == 0.0

    def test_extraction_result_with_data(self):
        """Test extraction result with entities and relations."""
        entity = EntityCreate(name="Test", entity_type="concept")
        relation = RelationCreate(
            subject_id=1,
            object_id=2,
            predicate="relates_to"
        )
        result = ExtractionResult(
            entities=[entity],
            relations=[relation],
            confidence_score=0.75
        )
        assert len(result.entities) == 1
        assert len(result.relations) == 1
        assert result.confidence_score == 0.75
