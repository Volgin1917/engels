"""
Context builder for RAG engine.
Assembles relevant context from search results for LLM prompting.
"""

from datetime import datetime
from typing import Any

import structlog

logger = structlog.get_logger(__name__)


class ContextBuilder:
    """
    Builds optimized context for RAG (Retrieval-Augmented Generation).
    Combines search results into coherent context with proper formatting.
    """

    def __init__(
        self,
        max_context_length: int = 4000,
        include_metadata: bool = True,
        chunk_separator: str = "\n\n---\n\n",
    ):
        """
        Initialize context builder.

        Args:
            max_context_length: Maximum context length in characters
            include_metadata: Include source metadata in context
            chunk_separator: Separator between chunks
        """
        self.max_context_length = max_context_length
        self.include_metadata = include_metadata
        self.chunk_separator = chunk_separator

        logger.info(
            "ContextBuilder initialized",
            max_context_length=max_context_length,
            include_metadata=include_metadata,
        )

    def build_context(
        self, search_results: list[dict[str, Any]], query: str | None = None
    ) -> dict[str, Any]:
        """
        Build context from search results.

        Args:
            search_results: List of search result dicts from SemanticSearchService
            query: Original query string (optional, for context header)

        Returns:
            Dict with assembled context and metadata
        """
        if not search_results:
            logger.warning("No search results provided for context building")
            return {
                "context_text": "",
                "chunks_used": 0,
                "total_chunks": 0,
                "truncated": False,
                "sources": [],
                "metadata": {"query": query, "built_at": datetime.utcnow().isoformat()},
            }

        logger.info(
            "Building context", total_chunks=len(search_results), max_length=self.max_context_length
        )

        context_parts = []
        current_length = 0
        chunks_used = 0
        sources_map = {}  # Track unique sources

        # Add header if query provided
        if query:
            header = f"Контекст для запроса: {query}\n\n"
            current_length += len(header)
            context_parts.append(header)

        # Add chunks until we reach max length
        for result in search_results:
            chunk_text = result.get("text", "")
            source_title = result.get("source_title", "Unknown Source")
            chunk_index = result.get("chunk_index", 0)
            similarity = result.get("similarity", 0.0)
            source_id = result.get("source_id")

            # Track sources
            if source_id not in sources_map:
                sources_map[source_id] = {"title": source_title, "id": source_id, "chunks_count": 0}
            sources_map[source_id]["chunks_count"] += 1

            # Format chunk with metadata
            if self.include_metadata:
                formatted_chunk = (
                    f"[Источник: {source_title}, Чанк #{chunk_index}, "
                    f"Релевантность: {similarity:.2f}]\n{chunk_text}"
                )
            else:
                formatted_chunk = chunk_text

            # Check if adding this chunk would exceed limit
            potential_length = current_length + len(formatted_chunk) + len(self.chunk_separator)

            if potential_length > self.max_context_length and chunks_used > 0:
                logger.info(
                    "Context length limit reached",
                    current_length=current_length,
                    chunks_used=chunks_used,
                )
                break

            context_parts.append(formatted_chunk)
            context_parts.append(self.chunk_separator)
            current_length += len(formatted_chunk) + len(self.chunk_separator)
            chunks_used += 1

        # Remove trailing separator
        if context_parts and context_parts[-1] == self.chunk_separator:
            context_parts.pop()
            current_length -= len(self.chunk_separator)

        context_text = "".join(context_parts)

        # Build result
        result = {
            "context_text": context_text,
            "chunks_used": chunks_used,
            "total_chunks": len(search_results),
            "truncated": chunks_used < len(search_results),
            "sources": list(sources_map.values()),
            "metadata": {
                "query": query,
                "built_at": datetime.utcnow().isoformat(),
                "context_length": current_length,
                "max_length": self.max_context_length,
            },
        }

        logger.info(
            "Context built successfully",
            chunks_used=chunks_used,
            context_length=current_length,
            truncated=result["truncated"],
        )

        return result

    def build_context_for_chat(
        self,
        search_results: list[dict[str, Any]],
        query: str,
        chat_history: list[dict[str, str]] | None = None,
    ) -> str:
        """
        Build context optimized for chat/conversation format.

        Args:
            search_results: Search results
            query: Current user query
            chat_history: Previous conversation turns (optional)

        Returns:
            Formatted context string for LLM prompt
        """
        context_data = self.build_context(search_results, query)

        if not context_data["context_text"]:
            return "Контекст не найден."

        # Format for chat
        lines = ["### Найденные материалы:", "", context_data["context_text"], "", "### Источники:"]

        for source in context_data["sources"]:
            lines.append(f"- {source['title']} ({source['chunks_count']} чанков)")

        if chat_history:
            lines.extend(
                [
                    "",
                    "### История диалога:",
                ]
            )
            for turn in chat_history[-3:]:  # Last 3 turns
                role = "Пользователь" if turn["role"] == "user" else "Ассистент"
                lines.append(f"{role}: {turn['content']}")

        return "\n".join(lines)

    def estimate_tokens(self, text: str) -> int:
        """
        Estimate token count for a text (rough approximation).
        Uses average of 4 characters per token for Russian/English text.

        Args:
            text: Input text

        Returns:
            Estimated token count
        """
        # Rough estimation: ~4 chars per token for mixed RU/EN text
        return len(text) // 4

    def truncate_to_token_limit(
        self, context_data: dict[str, Any], token_limit: int
    ) -> dict[str, Any]:
        """
        Truncate context to fit within token limit.

        Args:
            context_data: Context dict from build_context
            token_limit: Maximum tokens allowed

        Returns:
            Truncated context dict
        """
        current_tokens = self.estimate_tokens(context_data["context_text"])

        if current_tokens <= token_limit:
            return context_data

        logger.warning(
            "Context exceeds token limit, truncating",
            current_tokens=current_tokens,
            limit=token_limit,
        )

        # Simple truncation by character count
        # (More sophisticated approaches could remove least relevant chunks)
        max_chars = token_limit * 4
        truncated_text = context_data["context_text"][:max_chars]

        # Try to cut at a sentence boundary
        last_period = truncated_text.rfind(".")
        if last_period > max_chars * 0.8:  # Don't cut too early
            truncated_text = truncated_text[: last_period + 1]

        context_data["context_text"] = truncated_text
        context_data["truncated"] = True
        context_data["metadata"]["truncated_by_tokens"] = True
        context_data["metadata"]["original_tokens"] = current_tokens
        context_data["metadata"]["final_tokens"] = self.estimate_tokens(truncated_text)

        return context_data
