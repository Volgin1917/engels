"""
Document ingestion service for Engels project.
Handles file upload, text extraction, and chunking.
"""

import re
from pathlib import Path

import structlog

logger = structlog.get_logger(__name__)


class TextChunker:
    """
    Splits text into overlapping chunks for embedding.
    Uses token-aware chunking with configurable size and overlap.
    """

    def __init__(self, chunk_size: int = 512, overlap_percent: float = 0.15):
        """
        Initialize chunker.

        Args:
            chunk_size: Target chunk size in tokens (approximate)
            overlap_percent: Overlap between chunks (0.0-1.0)
        """
        self.chunk_size = chunk_size
        self.overlap_percent = overlap_percent
        logger.debug(
            "TextChunker initialized", chunk_size=chunk_size, overlap_percent=overlap_percent
        )

    def _estimate_tokens(self, text: str) -> int:
        """Estimate token count (rough approximation: 1 token ≈ 4 chars)."""
        return len(text) // 4

    def _split_into_sentences(self, text: str) -> list[str]:
        """Split text into sentences while preserving boundaries."""
        # Simple sentence splitting - can be improved with nltk/spacy later
        sentences = re.split(r"(?<=[.!?])\s+", text.strip())
        return [s.strip() for s in sentences if s.strip()]

    def chunk_text(self, text: str) -> list[tuple[int, str]]:
        """
        Split text into overlapping chunks.

        Args:
            text: Input text to chunk

        Returns:
            List of (chunk_index, chunk_text) tuples
        """
        if not text or not text.strip():
            logger.warning("Empty text provided for chunking")
            return []

        sentences = self._split_into_sentences(text)
        if not sentences:
            return []

        chunks: list[tuple[int, str]] = []
        current_chunk: list[str] = []
        current_length = 0
        overlap_size = max(1, int(len(sentences) * self.overlap_percent))

        chunk_index = 0

        for sentence in sentences:
            sentence_tokens = self._estimate_tokens(sentence)

            # If adding this sentence exceeds chunk_size, save current chunk
            if current_length + sentence_tokens > self.chunk_size and current_chunk:
                chunk_text = " ".join(current_chunk)
                chunks.append((chunk_index, chunk_text))
                chunk_index += 1

                # Calculate overlap: keep last N sentences for next chunk
                overlap_start = max(0, len(current_chunk) - overlap_size)
                current_chunk = current_chunk[overlap_start:]
                current_length = sum(self._estimate_tokens(s) for s in current_chunk)

            current_chunk.append(sentence)
            current_length += sentence_tokens

        # Add remaining sentences as final chunk
        if current_chunk:
            chunk_text = " ".join(current_chunk)
            chunks.append((chunk_index, chunk_text))

        logger.info(
            "Text chunked successfully", total_chunks=len(chunks), original_length=len(text)
        )

        return chunks


class TextExtractor:
    """
    Extracts text from various file formats (PDF, DOCX, TXT, etc.).
    """

    SUPPORTED_EXTENSIONS = {".txt", ".pdf", ".docx", ".md", ".rst"}

    @classmethod
    def extract_from_file(cls, file_path: str) -> str | None:
        """
        Extract text from a file based on its extension.

        Args:
            file_path: Path to the file

        Returns:
            Extracted text or None if extraction failed
        """
        path = Path(file_path)
        ext = path.suffix.lower()

        if ext not in cls.SUPPORTED_EXTENSIONS:
            logger.warning(f"Unsupported file extension: {ext}")
            return None

        try:
            if ext == ".txt" or ext == ".md" or ext == ".rst":
                return cls._extract_txt(path)
            elif ext == ".pdf":
                return cls._extract_pdf(path)
            elif ext == ".docx":
                return cls._extract_docx(path)
            else:
                logger.error(f"No extractor implemented for: {ext}")
                return None
        except Exception as e:
            logger.error("Text extraction failed", file_path=str(path), error=str(e))
            return None

    @staticmethod
    def _extract_txt(path: Path) -> str:
        """Extract text from plain text files."""
        with open(path, encoding="utf-8") as f:
            return f.read()

    @staticmethod
    def _extract_pdf(path: Path) -> str:
        """
        Extract text from PDF files.
        Requires pdfplumber or PyMuPDF library.
        """
        try:
            import pdfplumber

            text_parts = []
            with pdfplumber.open(path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text_parts.append(page_text)
            return "\n".join(text_parts)
        except ImportError:
            logger.warning("pdfplumber not installed, PDF extraction unavailable")
            raise RuntimeError("Install pdfplumber: pip install pdfplumber")
        except Exception as e:
            logger.error("PDF extraction failed", path=str(path), error=str(e))
            raise

    @staticmethod
    def _extract_docx(path: Path) -> str:
        """
        Extract text from DOCX files.
        Requires python-docx library.
        """
        try:
            from docx import Document

            doc = Document(path)
            paragraphs = [para.text for para in doc.paragraphs if para.text.strip()]
            return "\n".join(paragraphs)
        except ImportError:
            logger.warning("python-docx not installed, DOCX extraction unavailable")
            raise RuntimeError("Install python-docx: pip install python-docx")
        except Exception as e:
            logger.error("DOCX extraction failed", path=str(path), error=str(e))
            raise


class IngestionService:
    """
    Main service for document ingestion pipeline.
    Coordinates extraction, chunking, and preparation for vectorization.
    """

    def __init__(self, chunk_size: int = 512, overlap_percent: float = 0.15):
        self.chunker = TextChunker(chunk_size=chunk_size, overlap_percent=overlap_percent)
        self.extractor = TextExtractor()
        logger.info("IngestionService initialized")

    def process_file(self, file_path: str) -> list[tuple[int, str]]:
        """
        Process a single file: extract text and chunk it.

        Args:
            file_path: Path to the file to process

        Returns:
            List of (chunk_index, chunk_text) tuples
        """
        logger.info("Processing file", file_path=file_path)

        # Extract text
        text = self.extractor.extract_from_file(file_path)
        if text is None:
            logger.error("Failed to extract text", file_path=file_path)
            return []

        logger.debug("Text extracted", length=len(text), file_path=file_path)

        # Chunk text
        chunks = self.chunker.chunk_text(text)

        logger.info("File processing completed", file_path=file_path, chunks_count=len(chunks))

        return chunks

    def process_text(self, text: str) -> list[tuple[int, str]]:
        """
        Process raw text: just chunk it.

        Args:
            text: Raw text to chunk

        Returns:
            List of (chunk_index, chunk_text) tuples
        """
        logger.debug("Processing raw text", length=len(text))
        return self.chunker.chunk_text(text)
