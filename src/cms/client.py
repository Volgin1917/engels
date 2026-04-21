"""
Strapi CMS Client.
Handles API communication with Strapi backend.
"""
import httpx
import structlog
from typing import Any, Dict, List, Optional
from pydantic import BaseModel

logger = structlog.get_logger(__name__)


class StrapiConfig(BaseModel):
    """Configuration for Strapi client."""
    base_url: str
    api_token: str
    timeout: int = 30


class StrapiClient:
    """
    Client for interacting with Strapi CMS.
    Supports CRUD operations and data synchronization.
    """

    def __init__(self, config: StrapiConfig):
        self.config = config
        self.base_url = config.base_url.rstrip("/")
        self.api_token = config.api_token
        self.timeout = config.timeout
        
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                headers={
                    "Authorization": f"Bearer {self.api_token}",
                    "Content-Type": "application/json",
                },
                timeout=httpx.Timeout(self.timeout),
            )
        return self._client

    async def close(self):
        """Close the HTTP client."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()

    async def get_entry(self, content_type: str, entry_id: int) -> Optional[Dict[str, Any]]:
        """
        Get a single entry from Strapi.
        
        Args:
            content_type: The content type (e.g., 'entities', 'relations')
            entry_id: The ID of the entry
            
        Returns:
            Entry data or None if not found
        """
        client = await self._get_client()
        try:
            response = await client.get(f"/api/{content_type}/{entry_id}")
            response.raise_for_status()
            data = response.json()
            return data.get("data")
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                logger.warning(f"Entry {entry_id} not found in {content_type}")
                return None
            logger.error(f"Error fetching entry {entry_id}: {e}")
            raise

    async def find_entries(
        self, 
        content_type: str, 
        filters: Optional[Dict[str, Any]] = None,
        fields: Optional[List[str]] = None,
        populate: Optional[List[str]] = None,
        pagination: Optional[Dict[str, int]] = None
    ) -> List[Dict[str, Any]]:
        """
        Find multiple entries with filters.
        
        Args:
            content_type: The content type
            filters: Query filters
            fields: Fields to return
            populate: Relations to populate
            pagination: Pagination settings
            
        Returns:
            List of entries
        """
        client = await self._get_client()
        params: Dict[str, Any] = {}
        
        if filters:
            params["filters"] = filters
        if fields:
            params["fields"] = ",".join(fields)
        if populate:
            params["populate"] = ",".join(populate)
        if pagination:
            params.update(pagination)
            
        try:
            response = await client.get(f"/api/{content_type}", params=params)
            response.raise_for_status()
            data = response.json()
            return data.get("data", [])
        except httpx.HTTPStatusError as e:
            logger.error(f"Error finding entries in {content_type}: {e}")
            raise

    async def create_entry(self, content_type: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new entry in Strapi.
        
        Args:
            content_type: The content type
            data: Entry data
            
        Returns:
            Created entry
        """
        client = await self._get_client()
        try:
            response = await client.post(f"/api/{content_type}", json={"data": data})
            response.raise_for_status()
            result = response.json()
            logger.info(f"Created entry in {content_type}", entry_id=result.get("data", {}).get("id"))
            return result.get("data", {})
        except httpx.HTTPStatusError as e:
            logger.error(f"Error creating entry in {content_type}: {e}")
            raise

    async def update_entry(
        self, 
        content_type: str, 
        entry_id: int, 
        data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update an existing entry in Strapi.
        
        Args:
            content_type: The content type
            entry_id: The ID of the entry
            data: Updated data
            
        Returns:
            Updated entry
        """
        client = await self._get_client()
        try:
            response = await client.put(f"/api/{content_type}/{entry_id}", json={"data": data})
            response.raise_for_status()
            result = response.json()
            logger.info(f"Updated entry in {content_type}", entry_id=entry_id)
            return result.get("data", {})
        except httpx.HTTPStatusError as e:
            logger.error(f"Error updating entry {entry_id} in {content_type}: {e}")
            raise

    async def delete_entry(self, content_type: str, entry_id: int) -> bool:
        """
        Delete an entry from Strapi.
        
        Args:
            content_type: The content type
            entry_id: The ID of the entry
            
        Returns:
            True if deleted successfully
        """
        client = await self._get_client()
        try:
            response = await client.delete(f"/api/{content_type}/{entry_id}")
            response.raise_for_status()
            logger.info(f"Deleted entry from {content_type}", entry_id=entry_id)
            return True
        except httpx.HTTPStatusError as e:
            logger.error(f"Error deleting entry {entry_id} from {content_type}: {e}")
            raise

    async def health_check(self) -> bool:
        """Check if Strapi is available."""
        client = await self._get_client()
        try:
            response = await client.get("/api/health")
            return response.status_code == 200
        except Exception:
            return False
