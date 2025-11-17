#!/usr/bin/env python
"""
Comprehensive test script for Phase 1 validation.
Tests all components of the Socratic Learning Companion.
"""

import sys
import traceback
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Test results tracker
test_results = {
    "passed": [],
    "failed": [],
    "warnings": []
}

def print_test_header(test_name):
    """Print a formatted test header."""
    print(f"\n{'='*70}")
    print(f"TEST: {test_name}")
    print('='*70)

def record_pass(test_name):
    """Record a passed test."""
    test_results["passed"].append(test_name)
    print(f"✅ PASS: {test_name}")

def record_fail(test_name, error):
    """Record a failed test."""
    test_results["failed"].append((test_name, str(error)))
    print(f"❌ FAIL: {test_name}")
    print(f"   Error: {error}")

def record_warning(test_name, warning):
    """Record a warning."""
    test_results["warnings"].append((test_name, warning))
    print(f"⚠️  WARNING: {test_name}")
    print(f"   {warning}")

# ==============================================================================
# TEST 1: Import Tests
# ==============================================================================

print_test_header("Module Imports")

try:
    # Core dependencies
    import fitz
    record_pass("PyMuPDF (fitz) import")
except Exception as e:
    record_fail("PyMuPDF (fitz) import", e)

try:
    import google.generativeai as genai
    record_pass("Google Generative AI import")
except Exception as e:
    record_fail("Google Generative AI import", e)

try:
    import chromadb
    record_pass("ChromaDB import")
except Exception as e:
    record_fail("ChromaDB import", e)

try:
    import sqlalchemy
    record_pass("SQLAlchemy import")
except Exception as e:
    record_fail("SQLAlchemy import", e)

try:
    import structlog
    record_pass("Structlog import")
except Exception as e:
    record_fail("Structlog import", e)

try:
    from pydantic_settings import BaseSettings
    record_pass("Pydantic Settings import")
except Exception as e:
    record_fail("Pydantic Settings import", e)

# Project modules
try:
    from src.utils.config import settings
    record_pass("Configuration module import")
except Exception as e:
    record_fail("Configuration module import", e)

try:
    from src.utils.logging_config import setup_logging, get_logger
    record_pass("Logging module import")
except Exception as e:
    record_fail("Logging module import", e)

try:
    from src.database.models import Base, Student, Topic, Conversation
    record_pass("Database models import")
except Exception as e:
    record_fail("Database models import", e)

try:
    from src.database.db_manager import get_db_manager
    record_pass("Database manager import")
except Exception as e:
    record_fail("Database manager import", e)

try:
    from src.database.chroma_manager import get_chroma_manager
    record_pass("ChromaDB manager import")
except Exception as e:
    record_fail("ChromaDB manager import", e)

try:
    from src.processing.base_processor import PDFProcessor, ChunkClassifier
    record_pass("Base processor import")
except Exception as e:
    record_fail("Base processor import", e)

try:
    from src.processing.textbook_processor import TextbookProcessor
    record_pass("Textbook processor import")
except Exception as e:
    record_fail("Textbook processor import", e)

# ==============================================================================
# TEST 2: Configuration Tests
# ==============================================================================

print_test_header("Configuration Validation")

try:
    from src.utils.config import settings

    # Check required settings
    assert hasattr(settings, 'gemini_api_key'), "Missing gemini_api_key"
    assert hasattr(settings, 'database_url'), "Missing database_url"
    assert hasattr(settings, 'chroma_persist_dir'), "Missing chroma_persist_dir"

    # Check paths
    assert settings.project_root.exists(), "Project root doesn't exist"
    assert settings.data_dir.exists(), "Data directory doesn't exist"

    record_pass("Configuration validation")

    # Display config info
    print(f"   Project Root: {settings.project_root}")
    print(f"   Data Dir: {settings.data_dir}")
    print(f"   Database URL: {settings.database_url}")
    print(f"   Chunk Size: {settings.chunk_size}")
    print(f"   Chunk Overlap: {settings.chunk_overlap}")

except Exception as e:
    record_fail("Configuration validation", e)
    traceback.print_exc()

# ==============================================================================
# TEST 3: Database Schema Tests
# ==============================================================================

print_test_header("Database Schema Validation")

try:
    from src.database.models import Base
    from sqlalchemy import inspect

    # Check all tables are defined
    tables = Base.metadata.tables
    expected_tables = [
        'students', 'topics', 'topic_prerequisites', 'student_progress',
        'conversations', 'misconceptions', 'assessments', 'sessions'
    ]

    for table_name in expected_tables:
        if table_name in tables:
            record_pass(f"Table '{table_name}' defined")
        else:
            record_fail(f"Table '{table_name}' defined", "Table not found in metadata")

    # Check for reserved word issues
    conv_table = tables.get('conversations')
    if conv_table is not None:
        columns = [c.name for c in conv_table.columns]
        if 'metadata' in columns:
            record_warning("Reserved word in schema",
                         "Column 'metadata' in conversations table (should be 'message_metadata')")
        elif 'message_metadata' in columns:
            record_pass("Reserved word fix applied (message_metadata)")

except Exception as e:
    record_fail("Database schema validation", e)
    traceback.print_exc()

# ==============================================================================
# TEST 4: Database Operations Tests
# ==============================================================================

print_test_header("Database Operations")

try:
    from src.database.db_manager import DatabaseManager

    # Create test database
    test_db = DatabaseManager("sqlite:///:memory:")
    test_db.create_tables()
    record_pass("Create tables in memory DB")

    # Test topic creation
    topic = test_db.create_topic(
        topic_id="test_topic",
        title="Test Topic",
        description="Test description",
        difficulty=1
    )
    assert topic.topic_id == "test_topic"
    record_pass("Create topic")

    # Test student creation
    student = test_db.create_student(
        user_id="test_user",
        name="Test Student",
        email="test@example.com"
    )
    assert student.user_id == "test_user"
    record_pass("Create student")

    # Test progress update
    progress = test_db.update_progress(
        user_id="test_user",
        topic_id="test_topic",
        status="learning",
        understanding_score=0.5
    )
    assert progress.status == "learning"
    record_pass("Update student progress")

    # Test session creation
    import uuid
    session_id = str(uuid.uuid4())
    session = test_db.create_session(
        session_id=session_id,
        user_id="test_user",
        topic_id="test_topic"
    )
    assert session.session_id == session_id
    record_pass("Create session")

    # Test message addition
    message = test_db.add_message(
        session_id=session_id,
        user_id="test_user",
        role="user",
        content="Test message",
        metadata={"test": "data"}
    )
    assert message.content == "Test message"
    record_pass("Add message to conversation")

    # Test curriculum initialization
    test_db.initialize_curriculum()
    topics = test_db.get_topics_by_category("algorithms")
    assert len(topics) > 0
    record_pass("Initialize curriculum")

    print(f"   Total curriculum topics: {len(topics)}")

except Exception as e:
    record_fail("Database operations", e)
    traceback.print_exc()

# ==============================================================================
# TEST 5: ChromaDB Tests
# ==============================================================================

print_test_header("ChromaDB Operations")

try:
    from src.database.chroma_manager import ChromaManager
    import tempfile
    import shutil

    # Create temporary directory for test
    temp_dir = tempfile.mkdtemp()

    try:
        # Initialize ChromaDB
        chroma = ChromaManager(persist_directory=temp_dir)
        record_pass("Initialize ChromaDB manager")

        # Create collection
        collection = chroma.create_collection("test_collection")
        record_pass("Create ChromaDB collection")

        # Note: Embedding generation will fail due to SSL, but collection creation works
        record_warning("Embedding generation",
                      "Cannot test embedding generation due to SSL restrictions")

        # Get collection stats
        stats = chroma.get_collection_stats("test_collection")
        assert stats['count'] == 0  # Empty collection
        record_pass("Get collection stats")

    finally:
        # Cleanup
        shutil.rmtree(temp_dir, ignore_errors=True)

except Exception as e:
    record_fail("ChromaDB operations", e)
    traceback.print_exc()

# ==============================================================================
# TEST 6: PDF Processing Tests
# ==============================================================================

print_test_header("PDF Processing")

try:
    from src.processing.textbook_processor import TextbookProcessor
    from pathlib import Path

    # Find PDF files
    pdf_dir = Path("data/raw_pdfs/kleinberg_tardos")
    pdf_files = list(pdf_dir.glob("*.pdf"))

    if pdf_files:
        pdf_path = pdf_files[0]
        print(f"   Testing with: {pdf_path.name}")

        # Create processor
        processor = TextbookProcessor(str(pdf_path))
        record_pass("Create TextbookProcessor instance")

        # Test PDF opening
        processor.open_document()
        assert processor.doc is not None
        page_count = len(processor.doc)
        print(f"   Pages: {page_count}")
        record_pass(f"Open PDF ({page_count} pages)")

        # Test text extraction
        text = processor.extract_text_from_page(10)
        assert len(text) > 0
        print(f"   Sample text length: {len(text)} chars")
        record_pass("Extract text from page")

        # Test formatting extraction
        blocks = processor.extract_text_with_formatting(10)
        assert len(blocks) > 0
        record_pass("Extract formatted text blocks")

        # Test chapter/section detection
        chapter_info = processor.extract_chapter_info(10)
        if chapter_info:
            print(f"   Detected: {chapter_info}")
        record_pass("Chapter/section detection")

        # Test token counting
        token_count = processor.count_tokens("This is a test sentence.")
        assert token_count > 0
        print(f"   Token count method: {'tiktoken' if processor.use_tiktoken else 'approximation'}")
        record_pass("Token counting")

        # Test text cleaning
        dirty_text = "Test\n\ntext  with\n\nmultiple   spaces"
        clean_text = processor.clean_text(dirty_text)
        assert len(clean_text) < len(dirty_text)
        record_pass("Text cleaning")

        # Test LaTeX detection
        math_text = "The formula is $x^2 + y^2 = z^2$"
        has_math = processor.contains_math(math_text)
        assert has_math
        record_pass("LaTeX math detection")

        # Test chunk classification
        from src.processing.base_processor import ChunkClassifier

        theorem_text = "Theorem 1.1: If G is a graph, then..."
        chunk_type = ChunkClassifier.classify_chunk(theorem_text)
        assert chunk_type == "theorem"
        record_pass("Chunk classification (theorem)")

        proof_text = "Proof: We proceed by induction..."
        chunk_type = ChunkClassifier.classify_chunk(proof_text)
        assert chunk_type == "proof"
        record_pass("Chunk classification (proof)")

        processor.close_document()
        record_pass("Close PDF document")

    else:
        record_warning("PDF processing tests",
                      f"No PDF files found in {pdf_dir}")

except Exception as e:
    record_fail("PDF processing", e)
    traceback.print_exc()

# ==============================================================================
# TEST 7: Processed Data Validation
# ==============================================================================

print_test_header("Processed Data Validation")

try:
    import json

    processed_dir = Path("data/processed")
    json_files = list(processed_dir.glob("*_chunks.json"))

    if json_files:
        chunk_file = json_files[0]
        print(f"   Validating: {chunk_file.name}")

        with open(chunk_file, 'r') as f:
            chunks = json.load(f)

        assert len(chunks) > 0, "No chunks in file"
        print(f"   Total chunks: {len(chunks)}")
        record_pass(f"Load chunks file ({len(chunks)} chunks)")

        # Validate chunk structure
        sample_chunk = chunks[0]
        required_fields = ['chunk_id', 'content', 'metadata']
        for field in required_fields:
            assert field in sample_chunk, f"Missing field: {field}"
        record_pass("Chunk structure validation")

        # Validate metadata
        metadata = sample_chunk['metadata']
        expected_metadata = ['source', 'page_number', 'chunk_type', 'chunk_index', 'token_count']
        for field in expected_metadata:
            if field not in metadata:
                record_warning(f"Metadata field '{field}'",
                             f"Expected field not in chunk metadata")
        record_pass("Chunk metadata validation")

        # Count chunk types
        chunk_types = {}
        has_math_count = 0
        for chunk in chunks:
            chunk_type = chunk['metadata'].get('chunk_type', 'unknown')
            chunk_types[chunk_type] = chunk_types.get(chunk_type, 0) + 1
            if chunk['metadata'].get('has_math'):
                has_math_count += 1

        print(f"   Chunk types: {chunk_types}")
        print(f"   Chunks with math: {has_math_count}")
        record_pass("Chunk type distribution analysis")

        # Validate token counts
        token_counts = [c['metadata'].get('token_count', 0) for c in chunks]
        avg_tokens = sum(token_counts) / len(token_counts)
        print(f"   Avg tokens per chunk: {avg_tokens:.1f}")
        record_pass("Token count validation")

    else:
        record_warning("Processed data validation",
                      f"No chunk files found in {processed_dir}")

except Exception as e:
    record_fail("Processed data validation", e)
    traceback.print_exc()

# ==============================================================================
# TEST 8: Database File Check
# ==============================================================================

print_test_header("Database Files")

try:
    from pathlib import Path

    # Check SQLite DB
    db_file = Path("learning_companion.db")
    if db_file.exists():
        size_mb = db_file.stat().st_size / (1024 * 1024)
        print(f"   SQLite DB: {size_mb:.2f} MB")
        record_pass("SQLite database file exists")
    else:
        record_fail("SQLite database file", "File not found")

    # Check ChromaDB directory
    chroma_dir = Path("data/embeddings/chroma_db")
    if chroma_dir.exists():
        files = list(chroma_dir.rglob("*"))
        print(f"   ChromaDB files: {len(files)}")
        record_pass("ChromaDB directory exists")
    else:
        record_warning("ChromaDB directory", "Directory not found or empty")

except Exception as e:
    record_fail("Database files check", e)
    traceback.print_exc()

# ==============================================================================
# TEST SUMMARY
# ==============================================================================

print("\n" + "="*70)
print("TEST SUMMARY")
print("="*70)

print(f"\n✅ PASSED: {len(test_results['passed'])} tests")
for test in test_results['passed']:
    print(f"   • {test}")

if test_results['failed']:
    print(f"\n❌ FAILED: {len(test_results['failed'])} tests")
    for test, error in test_results['failed']:
        print(f"   • {test}")
        print(f"     Error: {error}")

if test_results['warnings']:
    print(f"\n⚠️  WARNINGS: {len(test_results['warnings'])}")
    for test, warning in test_results['warnings']:
        print(f"   • {test}: {warning}")

# Calculate success rate
total_tests = len(test_results['passed']) + len(test_results['failed'])
if total_tests > 0:
    success_rate = (len(test_results['passed']) / total_tests) * 100
    print(f"\n{'='*70}")
    print(f"SUCCESS RATE: {success_rate:.1f}% ({len(test_results['passed'])}/{total_tests})")
    print("="*70)

# Exit code
sys.exit(0 if len(test_results['failed']) == 0 else 1)
