"""
Vectorization service for Engels project.
Generates embeddings using Ollama and stores them in PostgreSQL.
"""
import structlog
from typing import List, Optional, Dict, Any
import httpx
from datetime import datetime

from backend.src.config import settings

logger = structlog.get_logger(__name__)


class OllamaClient:
    """
    Client for interacting with Ollama API.
    Handles embedding generation and model management.
    """
    
    def __init__(self, host: str = None, model: str = None):
        """
        Initialize Ollama client.
        
        Args:
            host: Ollama host URL (default from settings)
            model: Model name for embeddings (default from settings)
        """
        self.host = host or settings.ollama_host
        self.model = model or settings.ollama_model
        self.timeout = 60.0  # seconds
        
        logger.info(
            "OllamaClient initialized",
            host=self.host,
            model=self.model
        )
    
    async def generate_embedding(self, text: str) -> Optional[List[float]]:
        """
        Generate embedding for a single text.
        
        Args:
            text: Input text to embed
            
        Returns:
            Embedding vector or None if failed
        """
        url = f"{self.host}/api/embeddings"
        payload = {
            "model": self.model,
            "prompt": text
        }
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(url, json=payload)
                response.raise_for_status()
                result = response.json()
                embedding = result.get("embedding")
                
                if embedding:
                    logger.debug(
                        "Embedding generated",
                        text_length=len(text),
                        vector_dim=len(embedding)
                    )
                    return embedding
                else:
                    logger.error("No embedding in response", response=result)
                    return None
                    
        except httpx.TimeoutException:
            logger.error("Ollama request timeout", text_length=len(text))
            return None
        except httpx.HTTPStatusError as e:
            logger.error("Ollama HTTP error", status=e.response.status_code, error=str(e))
            return None
        except Exception as e:
            logger.error("Embedding generation failed", error=str(e))
            return None
    
    async def generate_embeddings_batch(
        self, 
        texts: List[str], 
        batch_size: int = 10
    ) -> List[Optional[List[float]]]:
        """
        Generate embeddings for multiple texts in batches.
        
        Args:
            texts: List of texts to embed
            batch_size: Number of concurrent requests
            
        Returns:
            List of embedding vectors (None for failed ones)
        """
        import asyncio
        
        semaphore = asyncio.Semaphore(batch_size)
        
        async def bounded_generate(text: str) -> Optional[List[float]]:
            async with semaphore:
                return await self.generate_embedding(text)
        
        tasks = [bounded_generate(text) for text in texts]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        embeddings = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error("Batch embedding failed", index=i, error=str(result))
                embeddings.append(None)
            else:
                embeddings.append(result)
        
        success_count = sum(1 for e in embeddings if e is not None)
        logger.info(
            "Batch embedding completed",
            total=len(texts),
            successful=success_count,
            failed=len(texts) - success_count
        )
        
        return embeddings
    
    def generate_embedding_sync(self, text: str) -> Optional[List[float]]:
        """
        Synchronous wrapper for generate_embedding.
        Use for non-async contexts.
        """
        import asyncio
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        return loop.run_until_complete(self.generate_embedding(text))
    
    async def check_health(self) -> bool:
        """Check if Ollama server is available."""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.host}/api/tags")
                return response.status_code == 200
        except Exception:
            return False
    
    async def list_models(self) -> List[str]:
        """List available models on Ollama server."""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{self.host}/api/tags")
                response.raise_for_status()
                result = response.json()
                models = [model["name"] for model in result.get("models", [])]
                logger.info("Available models", models=models)
                return models
        except Exception as e:
            logger.error("Failed to list models", error=str(e))
            return []
    
    async def pull_model(self, model_name: str) -> bool:
        """
        Pull a model from Ollama library.
        
        Args:
            model_name: Name of the model to pull
            
        Returns:
            True if successful, False otherwise
        """
        url = f"{self.host}/api/pull"
        payload = {"name": model_name}
        
        try:
            async with httpx.AsyncClient(timeout=300.0) as client:
                response = await client.post(url, json=payload)
                response.raise_for_status()
                logger.info("Model pulled successfully", model=model_name)
                return True
        except Exception as e:
            logger.error("Failed to pull model", model=model_name, error=str(e))
            return False


class VectorizationService:
    """
    Main service for vectorizing text chunks.
    Coordinates embedding generation and database storage.
    """
    
    def __init__(self, ollama_client: Optional[OllamaClient] = None):
        """
        Initialize vectorization service.
        
        Args:
            ollama_client: OllamaClient instance (created if not provided)
        """
        self.client = ollama_client or OllamaClient()
        logger.info("VectorizationService initialized")
    
    async def vectorize_chunks(
        self, 
        chunks: List[tuple], 
        source_id: int
    ) -> List[Dict[str, Any]]:
        """
        Generate embeddings for text chunks.
        
        Args:
            chunks: List of (chunk_index, chunk_text) tuples
            source_id: ID of the source document
            
        Returns:
            List of dicts with chunk data and embeddings
        """
        if not chunks:
            logger.warning("No chunks to vectorize")
            return []
        
        texts = [text for _, text in chunks]
        indices = [idx for idx, _ in chunks]
        
        logger.info(
            "Starting vectorization",
            source_id=source_id,
            chunk_count=len(chunks)
        )
        
        embeddings = await self.client.generate_embeddings_batch(texts)
        
        results = []
        for i, (idx, text) in enumerate(chunks):
            embedding = embeddings[i]
            results.append({
                "source_id": source_id,
                "chunk_index": idx,
                "text": text,
                "embedding": embedding,
                "created_at": datetime.utcnow()
            })
        
        success_count = sum(1 for r in results if r["embedding"] is not None)
        logger.info(
            "Vectorization completed",
            source_id=source_id,
            total=len(chunks),
            successful=success_count
        )
        
        return results
    
    def vectorize_chunks_sync(
        self, 
        chunks: List[tuple], 
        source_id: int
    ) -> List[Dict[str, Any]]:
        """
        Synchronous wrapper for vectorize_chunks.
        """
        import asyncio
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        return loop.run_until_complete(self.vectorize_chunks(chunks, source_id))
    
    async def verify_and_prepare_model(self) -> bool:
        """
        Verify Ollama is running and required model is available.
        Pull model if needed.
        
        Returns:
            True if ready, False otherwise
        """
        # Check health
        is_healthy = await self.client.check_health()
        if not is_healthy:
            logger.error("Ollama server is not available")
            return False
        
        # Check if model exists
        models = await self.client.list_models()
        if self.client.model not in models:
            logger.warning(
                "Required model not found, attempting to pull",
                model=self.client.model
            )
            pulled = await self.client.pull_model(self.client.model)
            if not pulled:
                logger.error("Failed to pull model")
                return False
        
        logger.info("Ollama ready", model=self.client.model)
        return True
