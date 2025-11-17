"""Initialize database with schema and curriculum."""

from database.db_manager import get_db_manager
from database.chroma_manager import get_chroma_manager
from utils.logging_config import setup_logging, get_logger

setup_logging()
logger = get_logger(__name__)


def main():
    """Initialize all databases."""
    logger.info("Starting database initialization")

    # Initialize SQLite database
    logger.info("Initializing SQLite database")
    db_manager = get_db_manager()

    # Create tables
    logger.info("Creating database tables")
    db_manager.create_tables()

    # Initialize curriculum
    logger.info("Initializing curriculum")
    db_manager.initialize_curriculum()

    # Initialize ChromaDB
    logger.info("Initializing ChromaDB collections")
    chroma_manager = get_chroma_manager()
    chroma_manager.initialize_collections()

    logger.info("Database initialization complete")

    print("\n" + "="*60)
    print("DATABASE INITIALIZATION COMPLETE")
    print("="*60)
    print("\n✓ SQLite database created with tables:")
    print("  - students")
    print("  - topics")
    print("  - topic_prerequisites")
    print("  - student_progress")
    print("  - conversations")
    print("  - misconceptions")
    print("  - assessments")
    print("  - sessions")
    print("\n✓ Curriculum initialized with 8 topics from Kleinberg-Tardos")
    print("\n✓ ChromaDB collections created:")
    print("  - textbook_chunks")
    print("  - lecture_notes")
    print("  - prerequisite_concepts")
    print("\nNext step: Run 'python -m src.processing.process_pdfs' to process PDFs")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()
