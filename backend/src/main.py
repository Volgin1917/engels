"""
FastAPI application for Engels project.
Provides REST API for document ingestion, search, and RAG queries.
"""
import structlog
from contextlib import asynccontextmanager
from typing import List, Optional

from fastapi import FastAPI, HTTPException, BackgroundTasks, Query
from fastapi.middleware.cors import CORSMiddleware

from backend.src.schemas import (
    SourceCreate, Source, TextChunk, QueryRequest, QueryResponse, HealthResponse
)
from backend.src.rag_engine import RAGEngine
from backend.src.search import SemanticSearchService
from backend.src.vectorizer import VectorizationService, OllamaClient
from backend.src.config import settings
from backend.src.tasks import process_document

logger = structlog.get_logger(__name__)


# Global instances
rag_engine: Optional[RAGEngine] = None
search_service: Optional[SemanticSearchService] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize services on startup."""
    global rag_engine, search_service
    
    logger.info("Starting Engels API server")
    
    # Initialize services
    search_service = SemanticSearchService()
    rag_engine = RAGEngine(
        db_url=settings.database_url,
        ollama_host=settings.ollama_host,
        ollama_model=settings.ollama_model,
        top_k=5
    )
    
    logger.info("Services initialized successfully")
    
    yield
    
    logger.info("Shutting down Engels API server")


app = FastAPI(
    title="Engels API",
    description="RAG-based knowledge extraction and question answering system",
    version="0.2.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Root endpoint with API info."""
    return {
        "name": "Engels API",
        "version": "0.2.0",
        "description": "RAG-based knowledge extraction and question answering",
        "docs": "/docs"
    }


@app.post("/api/v1/query", response_model=QueryResponse)
async def query_knowledge(request: QueryRequest):
    """
    Ask a question and get an answer based on retrieved context.
    
    This endpoint performs:
    1. Semantic search for relevant chunks
    2. Context assembly
    3. LLM-based answer generation
    
    Returns the answer along with sources and metadata.
    """
    if not rag_engine:
        raise HTTPException(status_code=503, detail="RAG engine not initialized")
    
    try:
        result = await rag_engine.query(
            question=request.question,
            source_id=request.source_id,
            include_sources=request.include_sources,
            chat_history=None  # Can be extended for multi-turn conversations
        )
        
        return QueryResponse(
            answer=result["answer"],
            context=result["context"],
            sources=result["sources"],
            chunks_used=result["chunks_used"],
            metadata=result["metadata"]
        )
        
    except Exception as e:
        logger.error("Query failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Query processing failed: {str(e)}")


@app.get("/api/v1/search")
async def semantic_search(
    q: str = Query(..., description="Search query text"),
    top_k: int = Query(5, ge=1, le=20, description="Number of results"),
    source_id: Optional[int] = Query(None, description="Filter by source ID")
):
    """
    Perform semantic search without LLM generation.
    Returns relevant text chunks with similarity scores.
    """
    if not search_service:
        raise HTTPException(status_code=503, detail="Search service not initialized")
    
    try:
        # Use vectorizer to generate query embedding
        vectorizer = VectorizationService()
        results = search_service.search_by_text(
            query_text=q,
            vectorizer=vectorizer,
            top_k=top_k,
            source_id=source_id
        )
        
        return {
            "query": q,
            "results": results,
            "count": len(results)
        }
        
    except Exception as e:
        logger.error("Search failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@app.post("/api/v1/sources", response_model=Source)
async def create_source(source: SourceCreate, background_tasks: BackgroundTasks):
    """
    Register a new document source for processing.
    
    The actual file upload and processing happens asynchronously via Celery.
    """
    # TODO: Implement source creation with database storage
    # For now, return a placeholder
    logger.info("Source creation requested", title=source.title)
    
    # Placeholder - will be implemented with database integration
    raise HTTPException(
        status_code=501, 
        detail="Source creation not yet implemented. Use direct file upload."
    )


@app.post("/api/v1/process/{source_id}")
async def process_source(source_id: int, use_mcp: bool = False):
    """
    Trigger document processing for a source.
    Queues a Celery task for chunking, embedding, and entity extraction.
    """
    logger.info("Processing source", source_id=source_id, use_mcp=use_mcp)
    
    try:
        # Queue Celery task
        task = process_document.delay(source_id, use_mcp=use_mcp)
        
        return {
            "source_id": source_id,
            "task_id": task.id,
            "status": "queued"
        }
        
    except Exception as e:
        logger.error("Failed to queue processing task", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to start processing: {str(e)}")


@app.get("/api/v1/health", response_model=HealthResponse)
async def health_check():
    """
    Check health of all system components.
    """
    from datetime import datetime
    
    components = {
        "database": False,
        "ollama": False,
        "redis": False
    }
    
    try:
        # Check database
        if search_service:
            components["database"] = search_service.health_check()
        
        # Check Ollama
        if rag_engine:
            ollama_health = await rag_engine.vectorizer.client.check_health()
            components["ollama"] = ollama_health
        
        # Check Redis (Celery broker)
        try:
            import redis
            r = redis.Redis(
                host=settings.redis_host,
                port=settings.redis_port,
                db=0,
                decode_responses=False
            )
            r.ping()
            components["redis"] = True
        except Exception:
            components["redis"] = False
        
        overall_status = "healthy" if all(components.values()) else "degraded"
        
        return HealthResponse(
            status=overall_status,
            components=components,
            timestamp=datetime.utcnow()
        )
        
    except Exception as e:
        logger.error("Health check failed", error=str(e))
        return HealthResponse(
            status="unhealthy",
            components=components,
            timestamp=datetime.utcnow()
        )


@app.get("/api/v1/stats")
async def get_stats():
    """
    Get system statistics (document count, chunk count, etc.).
    """
    # TODO: Implement statistics from database
    return {
        "sources_count": 0,
        "chunks_count": 0,
        "entities_count": 0,
        "relations_count": 0,
        "message": "Statistics not yet implemented"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend.src.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
