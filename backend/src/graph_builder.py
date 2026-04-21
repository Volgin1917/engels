"""
Graph Builder Service for Engels Project
Builds and manages the knowledge graph from extracted entities and relations
"""

import hashlib
import logging
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from .entity_extractor import Entity, EntityType, Relation, get_entity_extractor
from .models import Entity as EntityModel
from .models import Relation as RelationModel

logger = logging.getLogger(__name__)


class GraphBuilder:
    """Service for building and managing the knowledge graph"""

    def __init__(self, db_session: AsyncSession):
        self.db = db_session
        self.extractor = get_entity_extractor()

    async def process_chunk_entities(
        self, chunk_id: int, text: str, source_id: int | None = None
    ) -> tuple[list[EntityModel], list[RelationModel]]:
        """
        Process a text chunk to extract and save entities and relations

        Args:
            chunk_id: ID of the text chunk
            text: Text content of the chunk
            source_id: Optional source document ID

        Returns:
            Tuple of (saved_entities, saved_relations)
        """
        # Extract entities and relations
        extraction_result = await self.extractor.extract_entities_and_relations(
            text=text, chunk_id=str(chunk_id)
        )

        # Deduplicate entities
        unique_entities = self.extractor.deduplicate_entities(
            extraction_result.entities, threshold=0.85
        )

        # Save to database
        saved_entities = await self._save_entities(unique_entities, source_id=source_id)

        saved_relations = await self._save_relations(
            extraction_result.relations, source_id=source_id
        )

        logger.info(
            f"Processed chunk {chunk_id}: "
            f"{len(saved_entities)} entities, {len(saved_relations)} relations"
        )

        return saved_entities, saved_relations

    async def _save_entities(
        self, entities: list[Entity], source_id: int | None = None
    ) -> list[EntityModel]:
        """Save or update entities in database"""

        saved_entities = []

        for entity in entities:
            # Generate hash for deduplication
            self._generate_entity_hash(entity.name, entity.entity_type)

            # Try to find existing entity
            stmt = select(EntityModel).where(
                EntityModel.name == entity.name, EntityModel.entity_type == entity.entity_type.value
            )

            result = await self.db.execute(stmt)
            existing_entity = result.scalar_one_or_none()

            if existing_entity:
                # Update existing entity
                existing_entity.description = entity.description or existing_entity.description
                current_count = existing_entity.extra_metadata.get("mentions_count", 0)
                mentions_count = current_count + len(entity.mentions)
                existing_entity.extra_metadata = {
                    **existing_entity.extra_metadata,
                    **entity.metadata,
                    "mentions_count": mentions_count,
                }

                # Flag for review if confidence is low or conflicting data
                if entity.confidence < 0.8 or entity.needs_review:
                    existing_entity.needs_review = True
                    existing_entity.review_comment = "Требуется проверка: обновлено из нового чанка"

                saved_entities.append(existing_entity)
            else:
                # Create new entity
                new_entity = EntityModel(
                    name=entity.name,
                    entity_type=entity.entity_type.value,
                    category=self._get_category_for_entity_type(entity.entity_type),
                    description=entity.description,
                    extra_metadata={
                        **entity.metadata,
                        "mentions": entity.mentions,
                        "mentions_count": len(entity.mentions),
                        "confidence": entity.confidence,
                    },
                    needs_review=entity.needs_review or entity.confidence < 0.8,
                )

                self.db.add(new_entity)
                saved_entities.append(new_entity)

        await self.db.flush()

        return saved_entities

    async def _save_relations(
        self, relations: list[Relation], source_id: int | None = None
    ) -> list[RelationModel]:
        """Save or update relations in database"""

        saved_relations = []

        for relation in relations:
            # Find subject and object entities
            subject_stmt = select(EntityModel).where(
                EntityModel.name == relation.source_entity,
            )
            object_stmt = select(EntityModel).where(
                EntityModel.name == relation.target_entity,
            )

            subject_result = await self.db.execute(subject_stmt)
            object_result = await self.db.execute(object_stmt)

            subject_entity = subject_result.scalar_one_or_none()
            object_entity = object_result.scalar_one_or_none()

            # Skip if either entity not found
            if not subject_entity or not object_entity:
                logger.debug(
                    f"Skipping relation: entity not found "
                    f"({relation.source_entity} -> {relation.target_entity})"
                )
                continue

            # Check for existing relation
            stmt = select(RelationModel).where(
                RelationModel.subject_id == subject_entity.id,
                RelationModel.object_id == object_entity.id,
                RelationModel.predicate == relation.relation_type.value,
            )

            result = await self.db.execute(stmt)
            existing_relation = result.scalar_one_or_none()

            if existing_relation:
                # Update existing relation
                existing_relation.confidence_score = max(
                    existing_relation.confidence_score, relation.confidence
                )
                existing_relation.extra_metadata = {
                    **existing_relation.extra_metadata,
                    **relation.metadata,
                }

                if relation.needs_review or relation.confidence < 0.7:
                    existing_relation.status = "raw"

                saved_relations.append(existing_relation)
            else:
                # Create new relation
                new_relation = RelationModel(
                    subject_id=subject_entity.id,
                    object_id=object_entity.id,
                    predicate=relation.relation_type.value,
                    confidence_score=relation.confidence,
                    evidence_quote=relation.description,
                    source_mcp=False,
                    source_id=source_id,
                    extra_metadata=relation.metadata,
                    status=(
                        "verified"
                        if relation.confidence >= 0.8 and not relation.needs_review
                        else "raw"
                    ),
                )

                self.db.add(new_relation)
                saved_relations.append(new_relation)

        await self.db.flush()

        return saved_relations

    def _generate_entity_hash(self, name: str, entity_type: EntityType) -> str:
        """Generate unique hash for entity deduplication"""
        key = f"{name.lower()}::{entity_type.value}"
        return hashlib.sha256(key.encode()).hexdigest()[:16]

    def _get_category_for_entity_type(self, entity_type: EntityType) -> str:
        """Map entity type to category"""
        category_map = {
            EntityType.CLASS: "social_class",
            EntityType.EPOCH: "historical_epoch",
            EntityType.MODE_OF_PRODUCTION: "production_mode",
            EntityType.PERSON: "person",
            EntityType.INSTITUTION: "institution",
            EntityType.CONCEPT: "concept",
            EntityType.EVENT: "event",
            EntityType.LOCATION: "location",
        }
        return category_map.get(entity_type, "other")

    async def get_entity_by_name(
        self, name: str, entity_type: str | None = None
    ) -> EntityModel | None:
        """Get entity by name and optional type"""

        stmt = select(EntityModel).where(EntityModel.name == name)

        if entity_type:
            stmt = stmt.where(EntityModel.entity_type == entity_type)

        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_entities_needing_review(self, limit: int = 100) -> list[EntityModel]:
        """Get entities flagged for manual review"""

        stmt = select(EntityModel).where(EntityModel.needs_review).limit(limit)

        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_relations_needing_review(self, limit: int = 100) -> list[RelationModel]:
        """Get relations flagged for manual review"""

        stmt = select(RelationModel).where(RelationModel.status == "raw").limit(limit)

        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def verify_entity(
        self, entity_id: int, verified: bool, comment: str | None = None
    ) -> bool:
        """Mark entity as verified or rejected"""

        stmt = select(EntityModel).where(EntityModel.id == entity_id)
        result = await self.db.execute(stmt)
        entity = result.scalar_one_or_none()

        if not entity:
            return False

        entity.needs_review = False
        entity.review_comment = comment
        entity.extra_metadata["verified_at"] = str(func.now())

        await self.db.flush()
        return True

    async def verify_relation(
        self, relation_id: int, verified: bool, comment: str | None = None
    ) -> bool:
        """Mark relation as verified or rejected"""

        stmt = select(RelationModel).where(RelationModel.id == relation_id)
        result = await self.db.execute(stmt)
        relation = result.scalar_one_or_none()

        if not relation:
            return False

        relation.status = "verified" if verified else "rejected"
        relation.extra_metadata["review_comment"] = comment

        await self.db.flush()
        return True

    async def get_graph_statistics(self) -> dict[str, Any]:
        """Get statistics about the knowledge graph"""

        # Count entities by type
        entity_type_stmt = select(EntityModel.entity_type, func.count(EntityModel.id)).group_by(
            EntityModel.entity_type
        )

        entity_type_result = await self.db.execute(entity_type_stmt)
        entities_by_type = dict(entity_type_result.all())

        # Count relations by predicate
        predicate_stmt = select(RelationModel.predicate, func.count(RelationModel.id)).group_by(
            RelationModel.predicate
        )

        predicate_result = await self.db.execute(predicate_stmt)
        relations_by_predicate = dict(predicate_result.all())

        # Count entities needing review
        review_stmt = select(func.count(EntityModel.id)).where(EntityModel.needs_review)
        review_result = await self.db.execute(review_stmt)
        entities_needing_review = review_result.scalar() or 0

        # Count raw relations
        raw_stmt = select(func.count(RelationModel.id)).where(RelationModel.status == "raw")
        raw_result = await self.db.execute(raw_stmt)
        raw_relations = raw_result.scalar() or 0

        return {
            "total_entities": sum(entities_by_type.values()),
            "entities_by_type": entities_by_type,
            "total_relations": sum(relations_by_predicate.values()),
            "relations_by_predicate": relations_by_predicate,
            "entities_needing_review": entities_needing_review,
            "raw_relations": raw_relations,
        }


def get_graph_builder(db_session: AsyncSession) -> GraphBuilder:
    """Create graph builder instance"""
    return GraphBuilder(db_session)
