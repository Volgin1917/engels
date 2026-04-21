"""
Data Synchronization between PostgreSQL and Strapi.
Handles bidirectional sync with conflict resolution.
"""
import structlog
from typing import Any, Dict, List, Optional
from datetime import datetime

from .client import StrapiClient

logger = structlog.get_logger(__name__)


class SyncConfig:
    """Configuration for data synchronization."""
    
    def __init__(
        self,
        batch_size: int = 100,
        conflict_resolution: str = "latest_wins",  # latest_wins, source_wins, manual
        sync_relations: bool = True,
        dry_run: bool = False
    ):
        self.batch_size = batch_size
        self.conflict_resolution = conflict_resolution
        self.sync_relations = sync_relations
        self.dry_run = dry_run


class DataSynchronizer:
    """
    Synchronizes data between PostgreSQL database and Strapi CMS.
    Supports full sync and incremental updates.
    """

    def __init__(self, strapi_client: StrapiClient, config: SyncConfig):
        self.strapi = strapi_client
        self.config = config

    async def sync_entity(
        self,
        entity_id: int,
        entity_data: Dict[str, Any],
        content_type: str = "entities"
    ) -> Dict[str, Any]:
        """
        Sync a single entity to Strapi.
        
        Args:
            entity_id: ID of the entity in PostgreSQL
            entity_data: Entity data from PostgreSQL
            content_type: Strapi content type
            
        Returns:
            Sync result with status and data
        """
        if self.config.dry_run:
            logger.info("Dry run: skipping sync", entity_id=entity_id)
            return {"status": "skipped", "reason": "dry_run"}

        # Check if entry exists in Strapi
        existing = await self.strapi.get_entry(content_type, entity_id)
        
        if existing:
            # Handle conflict resolution
            should_update = self._resolve_conflict(existing, entity_data)
            if should_update:
                updated = await self.strapi.update_entry(content_type, entity_id, entity_data)
                return {"status": "updated", "data": updated}
            else:
                return {"status": "unchanged", "data": existing}
        else:
            # Create new entry
            created = await self.strapi.create_entry(content_type, entity_data)
            return {"status": "created", "data": created}

    async def sync_entities_batch(
        self,
        entities: List[Dict[str, Any]],
        content_type: str = "entities"
    ) -> Dict[str, int]:
        """
        Sync a batch of entities to Strapi.
        
        Args:
            entities: List of entity data from PostgreSQL
            content_type: Strapi content type
            
        Returns:
            Statistics about the sync operation
        """
        stats = {"created": 0, "updated": 0, "unchanged": 0, "failed": 0}
        
        for entity in entities:
            try:
                result = await self.sync_entity(
                    entity_id=entity["id"],
                    entity_data=entity,
                    content_type=content_type
                )
                status = result["status"]
                if status in stats:
                    stats[status] += 1
            except Exception as e:
                logger.error("Failed to sync entity", entity_id=entity.get("id"), error=str(e))
                stats["failed"] += 1
        
        logger.info("Batch sync completed", stats=stats)
        return stats

    async def sync_full(
        self,
        get_all_entities_func,
        content_type: str = "entities"
    ) -> Dict[str, int]:
        """
        Perform full synchronization of all entities.
        
        Args:
            get_all_entities_func: Async function that returns all entities from PostgreSQL
            content_type: Strapi content type
            
        Returns:
            Statistics about the full sync
        """
        logger.info("Starting full sync", content_type=content_type)
        
        all_stats = {"created": 0, "updated": 0, "unchanged": 0, "failed": 0}
        
        # Fetch all entities in batches
        offset = 0
        while True:
            entities = await get_all_entities_func(
                limit=self.config.batch_size,
                offset=offset
            )
            
            if not entities:
                break
                
            batch_stats = await self.sync_entities_batch(entities, content_type)
            
            for key in all_stats:
                all_stats[key] += batch_stats.get(key, 0)
            
            offset += self.config.batch_size
        
        logger.info("Full sync completed", stats=all_stats)
        return all_stats

    def _resolve_conflict(
        self, 
        strapi_data: Dict[str, Any], 
        pg_data: Dict[str, Any]
    ) -> bool:
        """
        Resolve conflicts between Strapi and PostgreSQL data.
        
        Returns:
            True if PostgreSQL data should overwrite Strapi, False otherwise
        """
        resolution = self.config.conflict_resolution
        
        if resolution == "source_wins":
            return True
        elif resolution == "manual":
            # In manual mode, we don't auto-resolve
            logger.warning(
                "Conflict detected, manual resolution required",
                strapi_updated=strapi_data.get("updatedAt"),
                pg_updated=pg_data.get("updated_at")
            )
            return False
        else:  # latest_wins (default)
            strapi_updated = strapi_data.get("updatedAt") or strapi_data.get("updated_at")
            pg_updated = pg_data.get("updated_at") or pg_data.get("updatedAt")
            
            if not strapi_updated and not pg_updated:
                return True
            
            if not strapi_updated:
                return True
            if not pg_updated:
                return False
            
            # Compare timestamps
            try:
                strapi_time = self._parse_datetime(strapi_updated)
                pg_time = self._parse_datetime(pg_updated)
                return pg_time > strapi_time
            except Exception:
                logger.warning("Could not parse timestamps, defaulting to source_wins")
                return True

    def _parse_datetime(self, dt_string: str) -> datetime:
        """Parse datetime string from various formats."""
        formats = [
            "%Y-%m-%dT%H:%M:%S.%fZ",
            "%Y-%m-%dT%H:%M:%SZ",
            "%Y-%m-%dT%H:%M:%S.%f",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%d %H:%M:%S",
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(dt_string, fmt)
            except ValueError:
                continue
        
        raise ValueError(f"Unable to parse datetime: {dt_string}")

    async def sync_review_status(
        self,
        entity_id: int,
        needs_review: bool,
        reviewer_comment: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Update the review status of an entity in Strapi.
        
        Args:
            entity_id: ID of the entity
            needs_review: Whether the entity needs review
            reviewer_comment: Optional comment from reviewer
            
        Returns:
            Updated entity data
        """
        update_data = {
            "needs_review": needs_review,
            "reviewed_at": datetime.utcnow().isoformat() if not needs_review else None
        }
        
        if reviewer_comment is not None:
            update_data["reviewer_comment"] = reviewer_comment
        
        return await self.strapi.update_entry("entities", entity_id, update_data)
