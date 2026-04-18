"""
Semantic search service for Engels project.
Performs vector similarity search in PostgreSQL.
"""
import structlog
from typing import List, Dict, Any, Optional
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from backend.src.config import settings
from backend.src.models import TextChunk, Source

logger = structlog.get_logger(__name__)


class SemanticSearchService:
    """
    Service for performing semantic search using vector embeddings.
    Uses pgvector for efficient similarity search in PostgreSQL.
    """
    
    def __init__(self, db_url: str = None):
        """
        Initialize semantic search service.
        
        Args:
            db_url: Database connection URL (default from settings)
        """
        self.db_url = db_url or settings.database_url
        self.engine = create_engine(self.db_url)
        self.SessionLocal = sessionmaker(bind=self.engine, autoflush=False, autocommit=False)
        
        logger.info(
            "SemanticSearchService initialized",
            db_host=self.db_url.split("@")[-1].split("/")[0] if "@" in self.db_url else "localhost"
        )
    
    def search_similar(
        self, 
        query_embedding: List[float], 
        top_k: int = 5,
        source_id: Optional[int] = None,
        min_distance: float = 0.0,
        max_distance: float = 1.0
    ) -> List[Dict[str, Any]]:
        """
        Search for text chunks similar to the query embedding.
        
        Args:
            query_embedding: Query vector (must match embedding dimension)
            top_k: Number of results to return
            source_id: Optional filter by source document ID
            min_distance: Minimum distance threshold (0.0 = identical)
            max_distance: Maximum distance threshold (1.0 = completely different)
            
        Returns:
            List of dicts with chunk data and similarity scores
        """
        if not query_embedding:
            logger.error("Empty query embedding provided")
            return []
        
        embedding_dim = len(query_embedding)
        logger.info(
            "Starting semantic search",
            embedding_dim=embedding_dim,
            top_k=top_k,
            source_id=source_id
        )
        
        try:
            with self.SessionLocal() as session:
                # Build query with cosine distance
                # pgvector uses <=> for cosine distance (0 = identical, 2 = opposite)
                query_vector_str = "[" + ",".join(map(str, query_embedding)) + "]"
                
                sql = text("""
                    SELECT 
                        tc.id,
                        tc.source_id,
                        tc.chunk_index,
                        tc.text,
                        tc.created_at,
                        s.title as source_title,
                        (tc.embedding <=> :query_vector::vector) as distance
                    FROM text_chunks tc
                    JOIN sources s ON tc.source_id = s.id
                    WHERE tc.embedding IS NOT NULL
                    AND (tc.embedding <=> :query_vector::vector) BETWEEN :min_dist AND :max_dist
                    {source_filter}
                    ORDER BY distance ASC
                    LIMIT :top_k
                """).compile(
                    dialect=self.engine.dialect,
                    compile_kwargs={"literal_binds": True}
                )
                
                # Add source filter if provided
                source_filter = "AND tc.source_id = :source_id" if source_id else ""
                final_sql = text(str(sql).replace("{source_filter}", source_filter))
                
                params = {
                    "query_vector": query_vector_str,
                    "min_dist": min_distance,
                    "max_dist": max_distance,
                    "top_k": top_k
                }
                if source_id:
                    params["source_id"] = source_id
                
                result = session.execute(final_sql, params)
                rows = result.fetchall()
                
                results = []
                for row in rows:
                    results.append({
                        "id": row.id,
                        "source_id": row.source_id,
                        "chunk_index": row.chunk_index,
                        "text": row.text,
                        "created_at": row.created_at.isoformat() if row.created_at else None,
                        "source_title": row.source_title,
                        "distance": float(row.distance),
                        "similarity": 1.0 - float(row.distance) / 2.0  # Convert to similarity score
                    })
                
                logger.info(
                    "Semantic search completed",
                    results_count=len(results),
                    top_k=top_k
                )
                
                return results
                
        except Exception as e:
            logger.error("Semantic search failed", error=str(e))
            return []
    
    def search_by_text(
        self, 
        query_text: str, 
        vectorizer,
        top_k: int = 5,
        source_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Search by text query (generates embedding automatically).
        
        Args:
            query_text: Text query string
            vectorizer: VectorizationService instance for embedding generation
            top_k: Number of results to return
            source_id: Optional filter by source document ID
            
        Returns:
            List of dicts with chunk data and similarity scores
        """
        logger.info("Searching by text query", query_length=len(query_text))
        
        # Generate embedding for query
        embedding = vectorizer.client.generate_embedding_sync(query_text)
        
        if not embedding:
            logger.error("Failed to generate query embedding")
            return []
        
        return self.search_similar(
            query_embedding=embedding,
            top_k=top_k,
            source_id=source_id
        )
    
    def get_chunk_by_id(self, chunk_id: int) -> Optional[Dict[str, Any]]:
        """
        Get a specific chunk by ID.
        
        Args:
            chunk_id: Chunk database ID
            
        Returns:
            Chunk data or None if not found
        """
        try:
            with self.SessionLocal() as session:
                chunk = session.query(TextChunk).filter(TextChunk.id == chunk_id).first()
                
                if not chunk:
                    logger.warning("Chunk not found", chunk_id=chunk_id)
                    return None
                
                source = session.query(Source).filter(Source.id == chunk.source_id).first()
                
                return {
                    "id": chunk.id,
                    "source_id": chunk.source_id,
                    "chunk_index": chunk.chunk_index,
                    "text": chunk.text,
                    "embedding": chunk.embedding,
                    "created_at": chunk.created_at.isoformat() if chunk.created_at else None,
                    "source_title": source.title if source else None
                }
        except Exception as e:
            logger.error("Failed to get chunk", chunk_id=chunk_id, error=str(e))
            return None
    
    def health_check(self) -> bool:
        """Check if database connection is available."""
        try:
            with self.SessionLocal() as session:
                session.execute(text("SELECT 1"))
                return True
        except Exception as e:
            logger.error("Database health check failed", error=str(e))
            return False
