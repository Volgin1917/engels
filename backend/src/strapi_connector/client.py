"""
Async HTTP client for Strapi CMS API.
Handles authentication and CRUD operations for entities, relations, and documents.
"""

from typing import Any

import httpx
import structlog

logger = structlog.get_logger(__name__)


class StrapiClient:
    """Async client for Strapi CMS REST API."""

    def __init__(
        self,
        base_url: str = "http://strapi:1337",
        api_token: str | None = None,
        timeout: float = 30.0,
    ):
        self.base_url = base_url.rstrip("/")
        self.api_token = api_token
        self.timeout = timeout
        self._client: httpx.AsyncClient | None = None

    async def __aenter__(self):
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.disconnect()

    async def connect(self):
        """Initialize HTTP client session."""
        headers = {}
        if self.api_token:
            headers["Authorization"] = f"Bearer {self.api_token}"

        self._client = httpx.AsyncClient(
            base_url=self.base_url, headers=headers, timeout=self.timeout
        )
        logger.info("Strapi client connected", base_url=self.base_url)

    async def disconnect(self):
        """Close HTTP client session."""
        if self._client:
            await self._client.aclose()
            logger.info("Strapi client disconnected")

    async def health_check(self) -> bool:
        """Check if Strapi CMS is available."""
        try:
            response = await self._client.get("/_health")
            return response.status_code == 200
        except Exception as e:
            logger.warning("Strapi health check failed", error=str(e))
            return False

    # Document operations
    async def create_document(
        self,
        title: str,
        content_type: str = "text",
        status: str = "pending",
        metadata: dict | None = None,
        external_id: str | None = None,
    ) -> dict[str, Any]:
        """Create a new document in Strapi."""
        payload = {
            "data": {
                "title": title,
                "content_type": content_type,
                "status": status,
                "metadata": metadata or {},
            }
        }
        if external_id:
            payload["data"]["external_id"] = external_id

        response = await self._client.post("/api/documents", json=payload)
        response.raise_for_status()
        result = response.json()
        logger.info("Document created", document_id=result.get("data", {}).get("id"))
        return result

    async def update_document_status(
        self, document_id: int, status: str, chunks_count: int = 0
    ) -> dict[str, Any]:
        """Update document processing status."""
        payload = {"data": {"status": status, "chunks_count": chunks_count}}

        response = await self._client.put(f"/api/documents/{document_id}", json=payload)
        response.raise_for_status()
        result = response.json()
        logger.info("Document status updated", document_id=document_id, status=status)
        return result

    async def get_document(self, document_id: int) -> dict[str, Any] | None:
        """Get document by ID with populated relations."""
        params = {"populate": ["entities", "relations"]}
        response = await self._client.get(f"/api/documents/{document_id}", params=params)

        if response.status_code == 404:
            return None

        response.raise_for_status()
        return response.json()

    # Entity operations
    async def create_entity(
        self,
        name: str,
        entity_type: str,
        description: str | None = None,
        metadata: dict | None = None,
        external_id: str | None = None,
    ) -> dict[str, Any]:
        """Create a new entity in Strapi."""
        payload = {
            "data": {
                "name": name,
                "type": entity_type,
                "description": description or "",
                "metadata": metadata or {},
            }
        }
        if external_id:
            payload["data"]["external_id"] = external_id

        response = await self._client.post("/api/entities", json=payload)
        response.raise_for_status()
        result = response.json()
        logger.info("Entity created", entity_id=result.get("data", {}).get("id"), name=name)
        return result

    async def get_or_create_entity(self, name: str, entity_type: str, **kwargs) -> dict[str, Any]:
        """Get existing entity or create new one."""
        # Search for existing entity
        params = {"filters[name][$eq]": name, "filters[type][$eq]": entity_type}
        response = await self._client.get("/api/entities", params=params)
        response.raise_for_status()
        result = response.json()

        if result.get("data"):
            return result["data"][0]

        # Create new entity
        return await self.create_entity(name=name, entity_type=entity_type, **kwargs)

    # Relation operations
    async def create_relation(
        self,
        from_entity_id: int,
        to_entity_id: int,
        relation_type: str,
        description: str | None = None,
        confidence: float | None = None,
        metadata: dict | None = None,
    ) -> dict[str, Any]:
        """Create a new relation between entities."""
        payload = {
            "data": {
                "from_entity": from_entity_id,
                "to_entity": to_entity_id,
                "relation_type": relation_type,
                "description": description or "",
                "metadata": metadata or {},
            }
        }
        if confidence is not None:
            payload["data"]["confidence"] = confidence

        response = await self._client.post("/api/relations", json=payload)
        response.raise_for_status()
        result = response.json()
        logger.info(
            "Relation created", from_id=from_entity_id, to_id=to_entity_id, type=relation_type
        )
        return result

    async def sync_graph_batch(
        self,
        entities: list[dict[str, Any]],
        relations: list[dict[str, Any]],
        document_id: int | None = None,
    ) -> dict[str, Any]:
        """
        Batch sync entities and relations to Strapi.
        Returns statistics about created/updated items.
        """
        stats = {"entities_created": 0, "entities_updated": 0, "relations_created": 0, "errors": []}

        # Process entities first
        entity_id_map = {}  # external_id -> strapi_id
        for entity_data in entities:
            try:
                external_id = entity_data.get("external_id")

                # Check if exists
                if external_id:
                    existing = await self._find_by_external_id("entity", external_id)
                    if existing:
                        entity_id_map[external_id] = existing["id"]
                        stats["entities_updated"] += 1
                        continue

                # Create new
                result = await self.create_entity(
                    name=entity_data["name"],
                    entity_type=entity_data["type"],
                    description=entity_data.get("description"),
                    metadata=entity_data.get("metadata"),
                    external_id=external_id,
                )
                strapi_id = result["data"]["id"]
                if external_id:
                    entity_id_map[external_id] = strapi_id
                stats["entities_created"] += 1

            except Exception as e:
                logger.error("Failed to sync entity", entity=entity_data, error=str(e))
                stats["errors"].append({"type": "entity", "data": entity_data, "error": str(e)})

        # Process relations
        for relation_data in relations:
            try:
                from_ext_id = relation_data.get("from_entity_external_id")
                to_ext_id = relation_data.get("to_entity_external_id")

                from_id = entity_id_map.get(from_ext_id)
                to_id = entity_id_map.get(to_ext_id)

                if not from_id or not to_id:
                    logger.warning("Skipping relation - entity not found", relation=relation_data)
                    continue

                await self.create_relation(
                    from_entity_id=from_id,
                    to_entity_id=to_id,
                    relation_type=relation_data["relation_type"],
                    description=relation_data.get("description"),
                    confidence=relation_data.get("confidence"),
                    metadata=relation_data.get("metadata"),
                )
                stats["relations_created"] += 1

            except Exception as e:
                logger.error("Failed to sync relation", relation=relation_data, error=str(e))
                stats["errors"].append({"type": "relation", "data": relation_data, "error": str(e)})

        # Update document if provided
        if document_id:
            try:
                await self.update_document_status(
                    document_id=document_id, status="completed", chunks_count=len(entities)
                )
            except Exception as e:
                logger.error("Failed to update document status", error=str(e))

        return stats

    async def _find_by_external_id(
        self, content_type: str, external_id: str
    ) -> dict[str, Any] | None:
        """Find item by external_id."""
        params = {"filters[external_id][$eq]": external_id}
        response = await self._client.get(f"/api/{content_type}s", params=params)
        response.raise_for_status()
        result = response.json()

        if result.get("data"):
            return result["data"][0]
        return None
