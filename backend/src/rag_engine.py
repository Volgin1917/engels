"""
RAG (Retrieval-Augmented Generation) engine for Engels project.
Combines semantic search with LLM generation.
"""

from datetime import datetime
from typing import Any

import structlog

from backend.src.config import settings
from backend.src.context_builder import ContextBuilder
from backend.src.search import SemanticSearchService
from backend.src.vectorizer import OllamaClient, VectorizationService

logger = structlog.get_logger(__name__)


class RAGEngine:
    """
    Main RAG engine for question answering.
    Orchestrates retrieval, context building, and LLM generation.
    """

    def __init__(
        self,
        db_url: str = None,
        ollama_host: str = None,
        ollama_model: str = None,
        max_context_length: int = 4000,
        top_k: int = 5,
    ):
        """
        Initialize RAG engine.

        Args:
            db_url: Database URL
            ollama_host: Ollama server host
            ollama_model: LLM model name for generation
            max_context_length: Maximum context length in characters
            top_k: Number of chunks to retrieve
        """
        self.top_k = top_k
        self.ollama_model = ollama_model or settings.ollama_model

        # Initialize services
        self.search_service = SemanticSearchService(db_url=db_url)
        self.vectorizer = VectorizationService(
            ollama_client=OllamaClient(host=ollama_host, model=ollama_model)
        )
        self.context_builder = ContextBuilder(max_context_length=max_context_length)

        logger.info(
            "RAGEngine initialized",
            model=self.ollama_model,
            top_k=top_k,
            max_context_length=max_context_length,
        )

    async def query(
        self,
        question: str,
        source_id: int | None = None,
        include_sources: bool = True,
        chat_history: list[dict[str, str]] | None = None,
    ) -> dict[str, Any]:
        """
        Process a query using RAG pipeline.

        Args:
            question: User question
            source_id: Optional filter by source document
            include_sources: Include source citations in response
            chat_history: Previous conversation turns (optional)

        Returns:
            Dict with answer, context, sources, and metadata
        """
        start_time = datetime.utcnow()
        logger.info("Starting RAG query", question_length=len(question))

        try:
            # Step 1: Generate embedding for the question
            logger.debug("Generating query embedding")
            query_embedding = await self.vectorizer.client.generate_embedding(question)

            if not query_embedding:
                logger.error("Failed to generate query embedding")
                return {
                    "answer": "Ошибка: не удалось обработать запрос.",
                    "context": "",
                    "sources": [],
                    "metadata": {
                        "error": "embedding_generation_failed",
                        "query": question,
                        "timestamp": start_time.isoformat(),
                    },
                }

            # Step 2: Search for relevant chunks
            logger.debug("Searching for relevant chunks", top_k=self.top_k)
            search_results = self.search_service.search_similar(
                query_embedding=query_embedding, top_k=self.top_k, source_id=source_id
            )

            if not search_results:
                logger.warning("No relevant chunks found")
                return {
                    "answer": "К сожалению, я не нашел релевантной информации по вашему вопросу.",
                    "context": "",
                    "sources": [],
                    "metadata": {
                        "chunks_found": 0,
                        "query": question,
                        "timestamp": start_time.isoformat(),
                    },
                }

            # Step 3: Build context
            logger.debug("Building context from search results")
            context_data = self.context_builder.build_context(
                search_results=search_results, query=question
            )

            # Step 4: Generate answer using LLM
            logger.debug("Generating answer with LLM")
            llm_response = await self._generate_answer(
                question=question, context=context_data["context_text"], chat_history=chat_history
            )

            # Step 5: Compile response
            end_time = datetime.utcnow()
            processing_time = (end_time - start_time).total_seconds()

            result = {
                "answer": llm_response.get("answer", ""),
                "context": context_data["context_text"],
                "sources": context_data["sources"] if include_sources else [],
                "chunks_used": context_data["chunks_used"],
                "metadata": {
                    "query": question,
                    "processing_time_seconds": processing_time,
                    "model_used": self.ollama_model,
                    "chunks_retrieved": len(search_results),
                    "timestamp": start_time.isoformat(),
                    **llm_response.get("metadata", {}),
                },
            }

            logger.info(
                "RAG query completed",
                processing_time=processing_time,
                chunks_used=context_data["chunks_used"],
                answer_length=len(result["answer"]),
            )

            return result

        except Exception as e:
            logger.error("RAG query failed", error=str(e))
            return {
                "answer": f"Произошла ошибка при обработке запроса: {str(e)}",
                "context": "",
                "sources": [],
                "metadata": {
                    "error": str(e),
                    "query": question,
                    "timestamp": start_time.isoformat(),
                },
            }

    async def _generate_answer(
        self, question: str, context: str, chat_history: list[dict[str, str]] | None = None
    ) -> dict[str, Any]:
        """
        Generate answer using Ollama LLM.

        Args:
            question: User question
            context: Retrieved context
            chat_history: Previous conversation turns

        Returns:
            Dict with answer and metadata
        """
        # Build prompt
        system_prompt = (
            "Ты — интеллектуальный ассистент системы Engels, специализирующийся на ответах "
            "на вопросы по философским и политическим текстам.\n"
            "Отвечай ТОЛЬКО на основе предоставленного контекста.\n"
            "Если ответ не найден в контексте, скажи об этом прямо.\n"
            "Будь точен, конкретен и цитируй источники когда это уместно."
        )

        if chat_history:
            # Format chat history
            history_lines = []
            for turn in chat_history[-5:]:  # Last 5 turns
                role = "Пользователь" if turn["role"] == "user" else "Ассистент"
                history_lines.append(f"{role}: {turn['content']}")
            history_text = "\n".join(history_lines)
            user_prompt = (
                f"{system_prompt}\n\n"
                f"### Контекст:\n{context}\n\n"
                f"### История диалога:\n{history_text}\n\n"
                f"### Текущий вопрос:\n{question}\n\n"
                f"Ответ:"
            )
        else:
            user_prompt = (
                f"{system_prompt}\n\n"
                f"### Контекст:\n{context}\n\n"
                f"### Вопрос:\n{question}\n\n"
                f"Ответ:"
            )

        # Call Ollama API
        try:
            import httpx

            url = f"{self.vectorizer.client.host}/api/generate"
            payload = {
                "model": self.ollama_model,
                "prompt": user_prompt,
                "stream": False,
                "options": {"temperature": 0.7, "top_p": 0.9, "num_predict": 512},
            }

            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(url, json=payload)
                response.raise_for_status()
                result = response.json()

                answer = result.get("response", "")

                logger.debug(
                    "LLM generation completed", answer_length=len(answer), model=self.ollama_model
                )

                return {
                    "answer": answer,
                    "metadata": {
                        "model": self.ollama_model,
                        "prompt_length": len(user_prompt),
                        "answer_length": len(answer),
                    },
                }

        except Exception as e:
            logger.error("LLM generation failed", error=str(e))
            return {"answer": f"Ошибка генерации ответа: {str(e)}", "metadata": {"error": str(e)}}

    def query_sync(
        self,
        question: str,
        source_id: int | None = None,
        include_sources: bool = True,
        chat_history: list[dict[str, str]] | None = None,
    ) -> dict[str, Any]:
        """
        Synchronous wrapper for query method.
        """
        import asyncio

        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        return loop.run_until_complete(
            self.query(question, source_id, include_sources, chat_history)
        )

    def health_check(self) -> dict[str, bool]:
        """
        Check health of all components.

        Returns:
            Dict with health status of each component
        """
        results = {
            "database": self.search_service.health_check(),
            "ollama": False,
            "overall": False,
        }

        # Check Ollama
        import asyncio

        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        results["ollama"] = loop.run_until_complete(self.vectorizer.client.check_health())
        results["overall"] = results["database"] and results["ollama"]

        logger.info("Health check completed", results=results)
        return results
