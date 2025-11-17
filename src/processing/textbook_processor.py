"""Textbook processor for Kleinberg-Tardos Algorithm Design book."""

import re
from typing import List, Dict, Any, Optional
import tiktoken

from .base_processor import PDFProcessor, TextChunk, ChunkClassifier
from ..utils.config import settings
from ..utils.logging_config import get_logger

logger = get_logger(__name__)


class TextbookProcessor(PDFProcessor):
    """
    Processor for Kleinberg-Tardos textbook using fixed-size chunking strategy.

    Chunks are created with:
    - Fixed token size (default 512 tokens)
    - Overlap between chunks (default 50 tokens)
    - Preserved LaTeX math notation
    - Preserved pseudocode formatting
    - Classified by type (theorem, proof, definition, etc.)
    """

    def __init__(
        self,
        pdf_path: str,
        chunk_size: int = None,
        chunk_overlap: int = None,
        max_chunk_size: int = None,
    ):
        """Initialize textbook processor."""
        super().__init__(pdf_path)

        self.chunk_size = chunk_size or settings.chunk_size
        self.chunk_overlap = chunk_overlap or settings.chunk_overlap
        self.max_chunk_size = max_chunk_size or settings.max_chunk_size

        # Use tiktoken for accurate token counting
        self.encoding = tiktoken.get_encoding("cl100k_base")

        self.logger = logger.bind(
            pdf_path=str(self.pdf_path),
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
        )

    def count_tokens(self, text: str) -> int:
        """Count tokens in text."""
        return len(self.encoding.encode(text))

    def extract_chapter_info(self, page_num: int) -> Optional[Dict[str, Any]]:
        """
        Extract chapter and section information from a page.
        Returns dict with chapter/section numbers and titles if found.
        """
        if not self.doc:
            self.open_document()

        blocks = self.extract_text_with_formatting(page_num)

        # Look for chapter/section markers in large font
        for block in blocks:
            text = block.get("text", "").strip()
            font_size = block.get("font_size", 0)

            # Chapter detection (usually largest font)
            chapter_match = re.match(r'Chapter\s+(\d+)[:\s]+(.+)', text, re.IGNORECASE)
            if chapter_match and font_size > 16:
                return {
                    "type": "chapter",
                    "number": int(chapter_match.group(1)),
                    "title": chapter_match.group(2).strip(),
                }

            # Section detection
            section_match = re.match(r'(\d+\.\d+)\s+(.+)', text)
            if section_match and font_size > 12:
                return {
                    "type": "section",
                    "number": section_match.group(1),
                    "title": section_match.group(2).strip(),
                }

        return None

    def detect_pseudocode_block(self, blocks: List[Dict[str, Any]]) -> bool:
        """Detect if blocks contain pseudocode based on formatting."""
        monospace_count = sum(
            1 for b in blocks if self.is_monospace(b.get("font_name", ""))
        )
        return monospace_count > len(blocks) * 0.5 if blocks else False

    def create_fixed_size_chunks(self, text: str, metadata: Dict[str, Any]) -> List[TextChunk]:
        """
        Create fixed-size chunks with overlap from text.

        Preserves:
        - LaTeX math expressions
        - Sentence boundaries
        - Paragraph structure where possible
        """
        # Split into sentences while preserving math
        sentences = self._split_into_sentences(text)

        chunks = []
        current_chunk = []
        current_tokens = 0

        for sentence in sentences:
            sentence_tokens = self.count_tokens(sentence)

            # If single sentence exceeds max chunk size, split it
            if sentence_tokens > self.max_chunk_size:
                # If we have accumulated content, save it first
                if current_chunk:
                    chunk_text = " ".join(current_chunk)
                    chunks.append(self._create_chunk(chunk_text, metadata, len(chunks)))
                    current_chunk = []
                    current_tokens = 0

                # Split the long sentence
                sub_chunks = self._split_long_sentence(sentence, metadata, len(chunks))
                chunks.extend(sub_chunks)
                continue

            # If adding this sentence exceeds chunk size, start new chunk
            if current_tokens + sentence_tokens > self.chunk_size and current_chunk:
                chunk_text = " ".join(current_chunk)
                chunks.append(self._create_chunk(chunk_text, metadata, len(chunks)))

                # Keep overlap: retain last few sentences
                overlap_sentences = self._get_overlap_sentences(current_chunk, self.chunk_overlap)
                current_chunk = overlap_sentences
                current_tokens = sum(self.count_tokens(s) for s in current_chunk)

            current_chunk.append(sentence)
            current_tokens += sentence_tokens

        # Add final chunk if any content remains
        if current_chunk:
            chunk_text = " ".join(current_chunk)
            chunks.append(self._create_chunk(chunk_text, metadata, len(chunks)))

        return chunks

    def _split_into_sentences(self, text: str) -> List[str]:
        """
        Split text into sentences while preserving LaTeX math.

        Handles:
        - Math expressions that might contain periods
        - Abbreviations (e.g., etc., i.e.)
        - Decimal numbers
        """
        # Temporarily replace math expressions with placeholders
        math_expressions = []
        def replace_math(match):
            math_expressions.append(match.group(0))
            return f"__MATH_{len(math_expressions)-1}__"

        # Replace display math $$...$$
        text = re.sub(r'\$\$[^\$]+\$\$', replace_math, text)
        # Replace inline math $...$
        text = re.sub(r'\$[^\$]+\$', replace_math, text)

        # Split on sentence boundaries
        # Match period, exclamation, or question mark followed by space and capital letter
        sentences = re.split(r'(?<=[.!?])\s+(?=[A-Z])', text)

        # Restore math expressions
        restored_sentences = []
        for sentence in sentences:
            for i, math_expr in enumerate(math_expressions):
                sentence = sentence.replace(f"__MATH_{i}__", math_expr)
            restored_sentences.append(sentence.strip())

        return [s for s in restored_sentences if s]

    def _split_long_sentence(
        self, sentence: str, metadata: Dict[str, Any], chunk_index: int
    ) -> List[TextChunk]:
        """Split a sentence that's too long into smaller chunks."""
        words = sentence.split()
        chunks = []
        current_words = []
        current_tokens = 0

        for word in words:
            word_tokens = self.count_tokens(word)

            if current_tokens + word_tokens > self.chunk_size and current_words:
                chunk_text = " ".join(current_words)
                chunks.append(self._create_chunk(chunk_text, metadata, chunk_index + len(chunks)))
                current_words = []
                current_tokens = 0

            current_words.append(word)
            current_tokens += word_tokens

        if current_words:
            chunk_text = " ".join(current_words)
            chunks.append(self._create_chunk(chunk_text, metadata, chunk_index + len(chunks)))

        return chunks

    def _get_overlap_sentences(self, sentences: List[str], overlap_tokens: int) -> List[str]:
        """Get the last few sentences that fit within overlap token limit."""
        overlap_sentences = []
        token_count = 0

        for sentence in reversed(sentences):
            sentence_tokens = self.count_tokens(sentence)
            if token_count + sentence_tokens > overlap_tokens:
                break
            overlap_sentences.insert(0, sentence)
            token_count += sentence_tokens

        return overlap_sentences

    def _create_chunk(
        self, text: str, base_metadata: Dict[str, Any], chunk_index: int
    ) -> TextChunk:
        """Create a TextChunk with classification and metadata."""
        # Classify chunk type
        chunk_type = ChunkClassifier.classify_chunk(text)

        # Extract mathematical concepts
        concepts = ChunkClassifier.extract_mathematical_concepts(text)

        # Check for math and pseudocode
        has_math = self.contains_math(text)

        # Build metadata
        metadata = {
            **base_metadata,
            "chunk_type": chunk_type,
            "chunk_index": chunk_index,
            "token_count": self.count_tokens(text),
            "has_math": has_math,
            "concepts": concepts if concepts else None,
        }

        return TextChunk(
            content=text,
            metadata=metadata,
            chunk_id=f"{self.pdf_path.stem}_chunk_{chunk_index}",
        )

    def process(self) -> List[TextChunk]:
        """Process the textbook PDF and return fixed-size chunks."""
        self.open_document()

        try:
            self.logger.info("Starting textbook processing")

            # Get document stats
            stats = self.get_document_stats()
            self.logger.info("Document stats", **stats)

            all_chunks = []
            current_chapter = None
            current_section = None

            for page_num in range(len(self.doc)):
                self.logger.debug(f"Processing page {page_num + 1}/{len(self.doc)}")

                # Check for chapter/section markers
                chapter_info = self.extract_chapter_info(page_num)
                if chapter_info:
                    if chapter_info["type"] == "chapter":
                        current_chapter = chapter_info
                        current_section = None
                        self.logger.info(
                            "Chapter detected",
                            chapter=chapter_info["number"],
                            title=chapter_info["title"],
                        )
                    elif chapter_info["type"] == "section":
                        current_section = chapter_info
                        self.logger.info(
                            "Section detected",
                            section=chapter_info["number"],
                            title=chapter_info["title"],
                        )

                # Extract text from page
                page_text = self.extract_text_from_page(page_num)
                if not page_text.strip():
                    continue

                # Clean text while preserving structure
                cleaned_text = self.clean_text(page_text)

                # Build metadata for this page
                page_metadata = {
                    "source": self.pdf_path.name,
                    "page_number": page_num + 1,
                    "chapter": current_chapter["number"] if current_chapter else None,
                    "chapter_title": current_chapter["title"] if current_chapter else None,
                    "section": current_section["number"] if current_section else None,
                    "section_title": current_section["title"] if current_section else None,
                }

                # Create chunks from page text
                page_chunks = self.create_fixed_size_chunks(cleaned_text, page_metadata)
                all_chunks.extend(page_chunks)

            self.logger.info(
                "Textbook processing complete",
                total_chunks=len(all_chunks),
                total_pages=len(self.doc),
                avg_chunks_per_page=len(all_chunks) / len(self.doc) if len(self.doc) > 0 else 0,
            )

            return all_chunks

        except Exception as e:
            self.logger.error("Error processing textbook", error=str(e))
            raise

        finally:
            self.close_document()
