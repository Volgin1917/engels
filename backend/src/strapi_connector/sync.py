"""
Graph synchronization service.
Coordinates sync between local graph representation and Strapi CMS.
"""
import hashlib
import structlog
from typing import List, Dict, Any, Optional

from backend.src.strapi_connector.client import StrapiClient
from backend.src.entity_extractor import Entity, Relation, EntityType

logger = structlog.get_logger(__name__)


class GraphSyncService:
    """Service for synchronizing knowledge graph with Strapi CMS."""
    
    def __init__(self, strapi_client: StrapiClient):
        self.strapi = strapi_client
    
    async def sync_document_graph(
        self,
        entities: List[Entity],
        relations: List[Relation],
        document_title: str,
        document_external_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Sync entities and relations from a document to Strapi.
        
        Args:
            entities: List of Entity objects
            relations: List of Relation objects
            document_title: Title of the source document
            document_external_id: Optional external ID for the document
            
        Returns:
            Statistics about the sync operation
        """
        logger.info(
            "Starting graph sync",
            entity_count=len(entities),
            relation_count=len(relations)
        )
        
        # Create or get document
        doc_result = await self.strapi.create_document(
            title=document_title,
            content_type="text",
            status="processing",
            metadata={"entity_count": len(entities), "relation_count": len(relations)},
            external_id=document_external_id
        )
        document_id = doc_result["data"]["id"]
        
        # Prepare entities for batch sync
        entities_data = []
        for entity in entities:
            ext_id = f"{entity.entity_type.value}_{hashlib.md5(entity.name.encode()).hexdigest()[:12]}"
            entities_data.append({
                "name": entity.name,
                "type": entity.entity_type.value,
                "description": entity.description,
                "metadata": entity.metadata,
                "external_id": ext_id
            })
        
        # Prepare relations for batch sync
        relations_data = []
        for rel in relations:
            from_ext_id = f"{EntityType.PERSON.value}_{hashlib.md5(rel.source_entity.encode()).hexdigest()[:12]}"
            to_ext_id = f"{EntityType.INSTITUTION.value}_{hashlib.md5(rel.target_entity.encode()).hexdigest()[:12]}"
            relations_data.append({
                "from_entity_external_id": from_ext_id,
                "to_entity_external_id": to_ext_id,
                "relation_type": rel.relation_type.value if hasattr(rel.relation_type, 'value') else str(rel.relation_type),
                "description": rel.description,
                "confidence": rel.confidence,
                "metadata": rel.metadata
            })
        
        # Batch sync to Strapi
        stats = await self.strapi.sync_graph_batch(
            entities=entities_data,
            relations=relations_data,
            document_id=document_id
        )
        
        logger.info(
            "Graph sync completed",
            **stats
        )
        
        return {
            "document_id": document_id,
            **stats
        }
    
    async def sync_entities_only(
        self,
        entities: List[Dict[str, Any]],
        document_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """Sync only entities without relations."""
        stats = {
            "entities_created": 0,
            "entities_updated": 0,
            "errors": []
        }
        
        for entity_data in entities:
            try:
                external_id = entity_data.get("external_id")
                
                if external_id:
                    existing = await self.strapi._find_by_external_id("entity", external_id)
                    if existing:
                        stats["entities_updated"] += 1
                        continue
                
                await self.strapi.create_entity(**entity_data)
                stats["entities_created"] += 1
                
            except Exception as e:
                logger.error("Failed to sync entity", entity=entity_data, error=str(e))
                stats["errors"].append({"data": entity_data, "error": str(e)})
        
        return stats
    
    async def health_check(self) -> bool:
        """Check if Strapi CMS is available."""
        return await self.strapi.health_check()
