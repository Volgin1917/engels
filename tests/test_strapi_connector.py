"""
Tests for Strapi CMS connector.
"""
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

from backend.src.strapi_connector.client import StrapiClient
from backend.src.strapi_connector.sync import GraphSyncService
from backend.src.entity_extractor import Entity, Relation, EntityType, RelationType


class TestStrapiClient:
    """Tests for StrapiClient."""
    
    @pytest.fixture
    def strapi_client(self):
        """Create a StrapiClient instance with mocked HTTP client."""
        client = StrapiClient(base_url="http://test-strapi:1337", api_token="test_token")
        return client
    
    @pytest.mark.asyncio
    async def test_client_initialization(self, strapi_client):
        """Test client initialization."""
        assert strapi_client.base_url == "http://test-strapi:1337"
        assert strapi_client.api_token == "test_token"
        assert strapi_client.timeout == 30.0
    
    @pytest.mark.asyncio
    async def test_health_check_success(self, strapi_client):
        """Test health check when Strapi is available."""
        mock_response = AsyncMock()
        mock_response.status_code = 200
        
        with patch.object(strapi_client, '_client') as mock_client:
            mock_client.get = AsyncMock(return_value=mock_response)
            result = await strapi_client.health_check()
            assert result is True
            mock_client.get.assert_called_once_with("/_health")
    
    @pytest.mark.asyncio
    async def test_health_check_failure(self, strapi_client):
        """Test health check when Strapi is unavailable."""
        with patch.object(strapi_client, '_client') as mock_client:
            mock_client.get = AsyncMock(side_effect=Exception("Connection refused"))
            result = await strapi_client.health_check()
            assert result is False
    
    @pytest.mark.asyncio
    async def test_create_document(self, strapi_client):
        """Test document creation."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": {"id": 1, "title": "Test Doc", "status": "pending"}
        }
        
        # Mock the _client before connecting
        mock_http_client = AsyncMock()
        mock_http_client.post = AsyncMock(return_value=mock_response)
        
        with patch.object(strapi_client, '_client', mock_http_client):
            result = await strapi_client.create_document(
                title="Test Doc",
                content_type="text",
                status="pending"
            )
            
            assert result["data"]["id"] == 1
            mock_http_client.post.assert_called_once()
            call_args = mock_http_client.post.call_args
            assert call_args[0][0] == "/api/documents"
            assert call_args[1]["json"]["data"]["title"] == "Test Doc"
    
    @pytest.mark.asyncio
    async def test_create_entity(self, strapi_client):
        """Test entity creation."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": {"id": 1, "name": "Test Entity", "type": "PERSON"}
        }
        
        # Mock the _client before connecting
        mock_http_client = AsyncMock()
        mock_http_client.post = AsyncMock(return_value=mock_response)
        
        with patch.object(strapi_client, '_client', mock_http_client):
            result = await strapi_client.create_entity(
                name="Test Entity",
                entity_type="PERSON",
                description="A test entity"
            )
            
            assert result["data"]["id"] == 1
            mock_http_client.post.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_or_create_entity_exists(self, strapi_client):
        """Test get_or_create_entity when entity exists."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": [{"id": 1, "name": "Existing Entity", "type": "PERSON"}]
        }
        
        # Mock the _client before connecting
        mock_http_client = AsyncMock()
        mock_http_client.get = AsyncMock(return_value=mock_response)
        
        with patch.object(strapi_client, '_client', mock_http_client):
            result = await strapi_client.get_or_create_entity(
                name="Existing Entity",
                entity_type="PERSON"
            )
            
            assert result["id"] == 1
            mock_http_client.get.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_or_create_entity_not_exists(self, strapi_client):
        """Test get_or_create_entity when entity doesn't exist."""
        # First call (get) returns empty
        mock_get_response = MagicMock()
        mock_get_response.status_code = 200
        mock_get_response.json.return_value = {"data": []}
        
        # Second call (create) returns new entity
        mock_create_response = MagicMock()
        mock_create_response.status_code = 200
        mock_create_response.json.return_value = {
            "data": {"id": 2, "name": "New Entity", "type": "PERSON"}
        }
        
        # Mock the _client before connecting
        mock_http_client = AsyncMock()
        mock_http_client.get = AsyncMock(return_value=mock_get_response)
        mock_http_client.post = AsyncMock(return_value=mock_create_response)
        
        with patch.object(strapi_client, '_client', mock_http_client):
            result = await strapi_client.get_or_create_entity(
                name="New Entity",
                entity_type="PERSON"
            )
            
            assert result["data"]["id"] == 2
            assert mock_http_client.get.call_count == 1
            assert mock_http_client.post.call_count == 1


class TestGraphSyncService:
    """Tests for GraphSyncService."""
    
    @pytest.fixture
    def mock_strapi_client(self):
        """Create a mocked StrapiClient."""
        client = AsyncMock(spec=StrapiClient)
        client.create_document = AsyncMock(return_value={"data": {"id": 1}})
        client.sync_graph_batch = AsyncMock(return_value={
            "entities_created": 2,
            "entities_updated": 0,
            "relations_created": 1,
            "errors": []
        })
        return client
    
    @pytest.mark.asyncio
    async def test_sync_document_graph(self, mock_strapi_client):
        """Test syncing a complete graph to Strapi."""
        service = GraphSyncService(mock_strapi_client)
        
        entities = [
            Entity(name="John Doe", entity_type=EntityType.PERSON, description="A person"),
            Entity(name="Acme Corp", entity_type=EntityType.INSTITUTION, description="A company")
        ]
        
        relations = [
            Relation(
                source_entity="John Doe",
                target_entity="Acme Corp",
                relation_type=RelationType.PARTICIPATES_IN
            )
        ]
        
        result = await service.sync_document_graph(
            entities=entities,
            relations=relations,
            document_title="Test Document"
        )
        
        assert result["document_id"] == 1
        assert result["entities_created"] == 2
        assert result["relations_created"] == 1
        mock_strapi_client.create_document.assert_called_once()
        mock_strapi_client.sync_graph_batch.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_sync_entities_only(self, mock_strapi_client):
        """Test syncing only entities."""
        service = GraphSyncService(mock_strapi_client)
        
        mock_strapi_client._find_by_external_id = AsyncMock(return_value=None)
        mock_strapi_client.create_entity = AsyncMock(return_value={"data": {"id": 1}})
        
        entities = [
            {"name": "Entity1", "type": "PERSON", "external_id": "ext_1"},
            {"name": "Entity2", "type": "LOCATION", "external_id": "ext_2"}
        ]
        
        result = await service.sync_entities_only(entities=entities)
        
        assert result["entities_created"] == 2
        assert mock_strapi_client.create_entity.call_count == 2
    
    @pytest.mark.asyncio
    async def test_health_check(self, mock_strapi_client):
        """Test health check delegation."""
        service = GraphSyncService(mock_strapi_client)
        mock_strapi_client.health_check = AsyncMock(return_value=True)
        
        result = await service.health_check()
        
        assert result is True
        mock_strapi_client.health_check.assert_called_once()
