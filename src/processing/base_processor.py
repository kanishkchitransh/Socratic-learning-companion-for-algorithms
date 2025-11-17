"""Base classes for PDF processing."""

import re
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from pathlib import Path

import fitz  # PyMuPDF

from ..utils.logging_config import get_logger

logger = get_logger(__name__)


@dataclass
class TextChunk:
    """Represents a chunk of text with metadata."""

    content: str
    metadata: Dict[str, Any]
    chunk_id: Optional[str] = None
    page_number: Optional[int] = None


class PDFProcessor(ABC):
    """Abstract base class for PDF processing."""

    def __init__(self, pdf_path: str):
        """Initialize PDF processor."""
        self.pdf_path = Path(pdf_path)
        self.doc: Optional[fitz.Document] = None
        self.logger = logger.bind(pdf_path=str(self.pdf_path))

        if not self.pdf_path.exists():
            raise FileNotFoundError(f"PDF not found: {self.pdf_path}")

    def open_document(self) -> None:
        """Open the PDF document."""
        try:
            self.doc = fitz.open(self.pdf_path)
            self.logger.info("PDF opened", page_count=len(self.doc))
        except Exception as e:
            self.logger.error("Error opening PDF", error=str(e))
            raise

    def close_document(self) -> None:
        """Close the PDF document."""
        if self.doc:
            self.doc.close()
            self.doc = None

    def extract_text_from_page(self, page_num: int) -> str:
        """Extract text from a single page."""
        if not self.doc:
            raise RuntimeError("Document not opened")

        try:
            page = self.doc[page_num]
            text = page.get_text()
            return text
        except Exception as e:
            self.logger.error("Error extracting text from page", page_num=page_num, error=str(e))
            return ""

    def extract_text_with_formatting(self, page_num: int) -> List[Dict[str, Any]]:
        """
        Extract text with formatting information (font size, style, etc.).
        Returns list of text blocks with formatting metadata.
        """
        if not self.doc:
            raise RuntimeError("Document not opened")

        try:
            page = self.doc[page_num]
            blocks = page.get_text("dict")["blocks"]

            formatted_blocks = []
            for block in blocks:
                if "lines" in block:
                    for line in block["lines"]:
                        for span in line["spans"]:
                            formatted_blocks.append({
                                "text": span["text"],
                                "font_size": span["size"],
                                "font_name": span["font"],
                                "flags": span["flags"],  # Bold, italic, etc.
                                "bbox": span["bbox"],
                            })

            return formatted_blocks
        except Exception as e:
            self.logger.error(
                "Error extracting formatted text",
                page_num=page_num,
                error=str(e)
            )
            return []

    def is_heading(self, block: Dict[str, Any], avg_font_size: float) -> bool:
        """Determine if a text block is likely a heading based on font size."""
        font_size = block.get("font_size", 0)
        # Heading if font size is significantly larger than average
        return font_size > avg_font_size * 1.2

    def is_monospace(self, font_name: str) -> bool:
        """Check if font is monospace (for code/pseudocode detection)."""
        monospace_fonts = [
            "courier",
            "mono",
            "consolas",
            "menlo",
            "monaco",
            "dejavu",
        ]
        font_lower = font_name.lower()
        return any(mono in font_lower for mono in monospace_fonts)

    def extract_latex_math(self, text: str) -> List[str]:
        """Extract LaTeX math expressions from text."""
        # Match inline math: $...$
        inline_math = re.findall(r'\$([^\$]+)\$', text)

        # Match display math: $$...$$
        display_math = re.findall(r'\$\$([^\$]+)\$\$', text)

        return inline_math + display_math

    def contains_math(self, text: str) -> bool:
        """Check if text contains LaTeX math notation."""
        return bool(re.search(r'\$[^\$]+\$', text) or re.search(r'\$\$[^\$]+\$\$', text))

    def clean_text(self, text: str) -> str:
        """Clean extracted text while preserving LaTeX and structure."""
        # Remove excessive whitespace but preserve paragraph breaks
        text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)

        # Remove hyphenation at line breaks (but not in compound words)
        text = re.sub(r'(\w+)-\n(\w+)', r'\1\2', text)

        # Remove single line breaks (join lines in same paragraph)
        # but preserve double line breaks (paragraph separation)
        lines = text.split('\n')
        cleaned_lines = []
        for i, line in enumerate(lines):
            if line.strip():
                cleaned_lines.append(line.strip())
            elif i > 0 and cleaned_lines:  # Preserve paragraph breaks
                cleaned_lines.append('')

        text = ' '.join(cleaned_lines)
        text = re.sub(r'  +', ' ', text)  # Multiple spaces to single

        return text.strip()

    @abstractmethod
    def process(self) -> List[TextChunk]:
        """Process the PDF and return chunks. Must be implemented by subclasses."""
        pass

    def get_document_stats(self) -> Dict[str, Any]:
        """Get statistics about the document."""
        if not self.doc:
            self.open_document()

        stats = {
            "page_count": len(self.doc),
            "file_size_mb": self.pdf_path.stat().st_size / (1024 * 1024),
            "file_name": self.pdf_path.name,
        }

        # Calculate average font size across first few pages
        font_sizes = []
        for page_num in range(min(5, len(self.doc))):
            blocks = self.extract_text_with_formatting(page_num)
            font_sizes.extend([b["font_size"] for b in blocks if "font_size" in b])

        if font_sizes:
            stats["avg_font_size"] = sum(font_sizes) / len(font_sizes)
            stats["max_font_size"] = max(font_sizes)
            stats["min_font_size"] = min(font_sizes)

        return stats


class ChunkClassifier:
    """Classifier for identifying chunk types."""

    @staticmethod
    def classify_chunk(text: str) -> str:
        """
        Classify chunk type based on content.

        Returns: 'theorem', 'proof', 'definition', 'example', 'exercise', 'general'
        """
        text_lower = text.lower()

        # Check for explicit labels
        if any(keyword in text_lower[:100] for keyword in ['theorem', 'lemma', 'corollary', 'proposition']):
            return 'theorem'

        if any(keyword in text_lower[:100] for keyword in ['proof:', 'proof.', 'proof ']):
            return 'proof'

        if any(keyword in text_lower[:100] for keyword in ['definition', 'define']):
            return 'definition'

        if any(keyword in text_lower[:100] for keyword in ['example', 'for instance', 'consider']):
            return 'example'

        if any(keyword in text_lower[:100] for keyword in ['exercise', 'problem', 'question']):
            return 'exercise'

        return 'general'

    @staticmethod
    def extract_mathematical_concepts(text: str) -> List[str]:
        """Extract key mathematical concepts from text."""
        concepts = []

        # Common algorithm/complexity terms
        patterns = [
            r'\b(O|Ω|Θ)\([^\)]+\)',  # Big-O notation
            r'\b(polynomial|exponential|logarithmic|linear|quadratic)\s+time\b',
            r'\b(NP-complete|NP-hard|P|NP)\b',
            r'\b(graph|tree|heap|array|list|queue|stack)\b',
            r'\b(sort|search|traverse|path|flow|matching)\b',
        ]

        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            concepts.extend(matches)

        return list(set(concepts))  # Remove duplicates
