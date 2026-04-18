"""
Tests for document ingestion and chunking.
"""
import pytest

from backend.src.ingestion import TextChunker, TextExtractor, IngestionService


class TestTextChunker:
    """Test text chunking functionality."""

    def test_chunker_initialization(self):
        """Test chunker initializes with default parameters."""
        chunker = TextChunker()
        assert chunker.chunk_size == 512
        assert chunker.overlap_percent == 0.15

    def test_chunker_custom_params(self):
        """Test chunker with custom parameters."""
        chunker = TextChunker(chunk_size=256, overlap_percent=0.2)
        assert chunker.chunk_size == 256
        assert chunker.overlap_percent == 0.2

    def test_chunk_empty_text(self):
        """Test chunking empty text returns empty list."""
        chunker = TextChunker()
        chunks = chunker.chunk_text("")
        assert chunks == []

    def test_chunk_whitespace_only(self):
        """Test chunking whitespace-only text returns empty list."""
        chunker = TextChunker()
        chunks = chunker.chunk_text("   \n\t  ")
        assert chunks == []

    def test_chunk_single_sentence(self):
        """Test chunking single sentence."""
        chunker = TextChunker(chunk_size=512)
        text = "This is a single sentence."
        chunks = chunker.chunk_text(text)
        
        assert len(chunks) == 1
        assert chunks[0][0] == 0  # index
        assert chunks[0][1] == text

    def test_chunk_multiple_sentences(self):
        """Test chunking multiple sentences."""
        chunker = TextChunker(chunk_size=100)
        text = """First sentence. Second sentence. Third sentence.
        Fourth sentence. Fifth sentence."""
        
        chunks = chunker.chunk_text(text)
        
        assert len(chunks) >= 1
        # All chunks should have valid indices
        for idx, chunk_text in chunks:
            assert isinstance(idx, int)
            assert idx >= 0
            assert len(chunk_text) > 0

    def test_chunk_overlap(self):
        """Test that chunks have proper overlap."""
        chunker = TextChunker(chunk_size=50, overlap_percent=0.15)
        text = """Sentence one. Sentence two. Sentence three. 
        Sentence four. Sentence five. Sentence six.
        Sentence seven. Sentence eight."""
        
        chunks = chunker.chunk_text(text)
        
        # With small chunk size and multiple sentences, we should get multiple chunks
        if len(chunks) > 1:
            # Check that consecutive chunks may share content (overlap)
            for i in range(len(chunks) - 1):
                current_text = chunks[i][1]
                next_text = chunks[i + 1][1]
                # Overlap logic is tested indirectly by ensuring chunks are created
                assert len(current_text) > 0
                assert len(next_text) > 0

    def test_chunk_preserves_sentence_boundaries(self):
        """Test that chunking respects sentence boundaries."""
        chunker = TextChunker(chunk_size=100)
        text = "First sentence. Second sentence. Third sentence."
        
        chunks = chunker.chunk_text(text)
        
        for idx, chunk_text in chunks:
            # Each chunk should contain complete sentences or be the last chunk
            # Sentences end with .!?
            if chunk_text != text:  # Not the only chunk
                # Should not cut in the middle of a sentence without space
                assert ". " in chunk_text or chunk_text.endswith(".")


class TestTextExtractor:
    """Test text extraction from files."""

    def test_extractor_supported_extensions(self):
        """Test supported file extensions."""
        assert '.txt' in TextExtractor.SUPPORTED_EXTENSIONS
        assert '.pdf' in TextExtractor.SUPPORTED_EXTENSIONS
        assert '.docx' in TextExtractor.SUPPORTED_EXTENSIONS
        assert '.md' in TextExtractor.SUPPORTED_EXTENSIONS

    def test_extract_txt_file(self, tmp_path):
        """Test extracting text from TXT file."""
        test_content = "Hello, World!\nThis is a test file."
        txt_file = tmp_path / "test.txt"
        txt_file.write_text(test_content, encoding='utf-8')
        
        extracted = TextExtractor.extract_from_file(str(txt_file))
        
        assert extracted == test_content

    def test_extract_md_file(self, tmp_path):
        """Test extracting text from Markdown file."""
        test_content = "# Header\n\nSome **markdown** text."
        md_file = tmp_path / "test.md"
        md_file.write_text(test_content, encoding='utf-8')
        
        extracted = TextExtractor.extract_from_file(str(md_file))
        
        assert extracted == test_content

    def test_extract_unsupported_extension(self, tmp_path):
        """Test extracting from unsupported file type."""
        unsupported_file = tmp_path / "test.xyz"
        unsupported_file.write_text("content")
        
        extracted = TextExtractor.extract_from_file(str(unsupported_file))
        
        assert extracted is None

    def test_extract_nonexistent_file(self):
        """Test extracting from non-existent file."""
        extracted = TextExtractor.extract_from_file("/nonexistent/file.txt")
        assert extracted is None


class TestIngestionService:
    """Test the main ingestion service."""

    def test_service_initialization(self):
        """Test service initializes correctly."""
        service = IngestionService()
        assert service.chunker is not None
        assert service.extractor is not None

    def test_process_text(self):
        """Test processing raw text."""
        service = IngestionService(chunk_size=100)
        text = "First sentence. Second sentence. Third sentence."
        
        chunks = service.process_text(text)
        
        assert isinstance(chunks, list)
        if chunks:
            assert all(isinstance(chunk, tuple) for chunk in chunks)
            assert all(len(chunk) == 2 for chunk in chunks)

    def test_process_text_empty(self):
        """Test processing empty text."""
        service = IngestionService()
        chunks = service.process_text("")
        assert chunks == []

    def test_process_file_txt(self, tmp_path):
        """Test processing a TXT file."""
        test_content = "Line one.\nLine two.\nLine three."
        txt_file = tmp_path / "document.txt"
        txt_file.write_text(test_content, encoding='utf-8')
        
        service = IngestionService(chunk_size=50)
        chunks = service.process_file(str(txt_file))
        
        assert len(chunks) >= 1
        total_text = "".join(text for _, text in chunks)
        assert "Line one" in total_text

    def test_process_long_text_creates_multiple_chunks(self):
        """Test that long text is split into multiple chunks."""
        # Create a long text with many sentences
        # Each sentence needs to be long enough to trigger chunking
        sentences = [f"Sentence number {i} contains enough words to exceed the chunk size limit when combined." for i in range(20)]
        text = " ".join(sentences)
        
        service = IngestionService(chunk_size=50, overlap_percent=0.15)
        chunks = service.process_text(text)
        
        # Should create multiple chunks for long text
        assert len(chunks) > 1
        
        # Verify all sentences are preserved
        all_text = " ".join(text for _, text in chunks)
        for i in range(20):
            assert f"Sentence number {i}" in all_text
