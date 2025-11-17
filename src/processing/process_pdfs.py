"""Main script to process PDFs and store in ChromaDB."""

import json
from pathlib import Path
from typing import List, Dict, Any
import time

from .textbook_processor import TextbookProcessor
from .base_processor import TextChunk
from ..database.chroma_manager import get_chroma_manager
from ..utils.config import settings
from ..utils.logging_config import get_logger, setup_logging

logger = get_logger(__name__)


class PDFPipeline:
    """Pipeline for processing PDFs and storing in vector database."""

    def __init__(self):
        """Initialize PDF processing pipeline."""
        self.chroma_manager = get_chroma_manager()
        self.processed_dir = settings.processed_dir
        self.processed_dir.mkdir(parents=True, exist_ok=True)

        logger.info("PDF Pipeline initialized")

    def process_textbook(self, pdf_path: Path) -> List[TextChunk]:
        """Process a textbook PDF and return chunks."""
        logger.info("Processing textbook", path=str(pdf_path))

        processor = TextbookProcessor(str(pdf_path))
        chunks = processor.process()

        logger.info(
            "Textbook processing complete",
            pdf=pdf_path.name,
            chunks=len(chunks),
        )

        return chunks

    def save_chunks_to_json(self, chunks: List[TextChunk], output_path: Path) -> None:
        """Save processed chunks to JSON for version control."""
        chunks_data = [
            {
                "chunk_id": chunk.chunk_id,
                "content": chunk.content,
                "metadata": chunk.metadata,
                "page_number": chunk.page_number,
            }
            for chunk in chunks
        ]

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(chunks_data, f, indent=2, ensure_ascii=False)

        logger.info("Chunks saved to JSON", path=str(output_path), count=len(chunks))

    def store_chunks_in_chroma(
        self, chunks: List[TextChunk], collection_name: str
    ) -> None:
        """Store chunks in ChromaDB with embeddings."""
        logger.info("Storing chunks in ChromaDB", collection=collection_name, count=len(chunks))

        # Prepare data for ChromaDB
        documents = [chunk.content for chunk in chunks]
        metadatas = [chunk.metadata for chunk in chunks]
        ids = [chunk.chunk_id for chunk in chunks]

        # Store in batches to avoid memory issues
        batch_size = 50
        for i in range(0, len(documents), batch_size):
            batch_docs = documents[i:i+batch_size]
            batch_metas = metadatas[i:i+batch_size]
            batch_ids = ids[i:i+batch_size]

            logger.info(
                "Storing batch",
                batch=i//batch_size + 1,
                total_batches=(len(documents) + batch_size - 1) // batch_size,
                batch_size=len(batch_docs),
            )

            self.chroma_manager.add_documents(
                collection_name=collection_name,
                documents=batch_docs,
                metadatas=batch_metas,
                ids=batch_ids,
            )

            # Small delay to avoid rate limiting
            time.sleep(1)

        logger.info("All chunks stored in ChromaDB", collection=collection_name)

    def process_kleinberg_tardos(self) -> Dict[str, Any]:
        """Process all Kleinberg-Tardos PDFs."""
        kt_dir = settings.kleinberg_tardos_dir
        pdf_files = list(kt_dir.glob("*.pdf"))

        if not pdf_files:
            logger.warning("No PDF files found in Kleinberg-Tardos directory", dir=str(kt_dir))
            return {"status": "no_files", "processed": 0}

        logger.info("Found PDF files", count=len(pdf_files), files=[f.name for f in pdf_files])

        all_chunks = []
        processing_stats = {
            "total_files": len(pdf_files),
            "processed_files": 0,
            "total_chunks": 0,
            "files": [],
        }

        for pdf_file in pdf_files:
            try:
                start_time = time.time()

                # Process PDF
                chunks = self.process_textbook(pdf_file)
                all_chunks.extend(chunks)

                processing_time = time.time() - start_time

                # Save chunks to JSON
                json_output = self.processed_dir / f"{pdf_file.stem}_chunks.json"
                self.save_chunks_to_json(chunks, json_output)

                # Update stats
                processing_stats["processed_files"] += 1
                processing_stats["total_chunks"] += len(chunks)
                processing_stats["files"].append({
                    "name": pdf_file.name,
                    "chunks": len(chunks),
                    "processing_time_seconds": round(processing_time, 2),
                })

                logger.info(
                    "PDF processed successfully",
                    file=pdf_file.name,
                    chunks=len(chunks),
                    time_seconds=round(processing_time, 2),
                )

            except Exception as e:
                logger.error("Error processing PDF", file=pdf_file.name, error=str(e))
                processing_stats["files"].append({
                    "name": pdf_file.name,
                    "error": str(e),
                })

        # Store all chunks in ChromaDB
        if all_chunks:
            logger.info("Storing all chunks in ChromaDB", total_chunks=len(all_chunks))
            self.store_chunks_in_chroma(all_chunks, "textbook_chunks")

        # Save processing stats
        stats_file = self.processed_dir / "processing_stats.json"
        with open(stats_file, 'w', encoding='utf-8') as f:
            json.dump(processing_stats, f, indent=2)

        logger.info("Processing complete", **processing_stats)

        return processing_stats

    def verify_chunk_quality(self) -> Dict[str, Any]:
        """Verify the quality of processed chunks."""
        logger.info("Verifying chunk quality")

        # Get collection stats
        stats = self.chroma_manager.get_collection_stats("textbook_chunks")

        # Test retrieval with sample queries
        sample_queries = [
            "What is dynamic programming?",
            "Explain the greedy algorithm approach",
            "How does network flow work?",
            "What is NP-completeness?",
        ]

        retrieval_results = []
        for query in sample_queries:
            try:
                results = self.chroma_manager.query(
                    collection_name="textbook_chunks",
                    query_text=query,
                    n_results=3,
                )

                retrieval_results.append({
                    "query": query,
                    "results_count": len(results['ids'][0]) if results['ids'] else 0,
                    "top_result_preview": results['documents'][0][0][:200] if results['documents'] and results['documents'][0] else None,
                })

                logger.info(
                    "Test query executed",
                    query=query,
                    results=len(results['ids'][0]) if results['ids'] else 0,
                )

            except Exception as e:
                logger.error("Error in test query", query=query, error=str(e))
                retrieval_results.append({
                    "query": query,
                    "error": str(e),
                })

        verification_report = {
            "collection_stats": stats,
            "sample_retrievals": retrieval_results,
        }

        # Save verification report
        report_file = self.processed_dir / "verification_report.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(verification_report, f, indent=2)

        logger.info("Chunk quality verification complete", report_path=str(report_file))

        return verification_report


def main():
    """Main entry point for PDF processing."""
    # Setup logging
    setup_logging()

    logger.info("Starting PDF processing pipeline")

    # Initialize pipeline
    pipeline = PDFPipeline()

    # Initialize ChromaDB collections
    logger.info("Initializing ChromaDB collections")
    pipeline.chroma_manager.initialize_collections()

    # Process Kleinberg-Tardos textbook
    logger.info("Processing Kleinberg-Tardos textbook")
    stats = pipeline.process_kleinberg_tardos()

    # Print summary
    print("\n" + "="*60)
    print("PDF PROCESSING SUMMARY")
    print("="*60)
    print(f"Total files processed: {stats['processed_files']}/{stats['total_files']}")
    print(f"Total chunks created: {stats['total_chunks']}")
    print("\nPer-file breakdown:")
    for file_info in stats['files']:
        if 'error' in file_info:
            print(f"  ❌ {file_info['name']}: ERROR - {file_info['error']}")
        else:
            print(f"  ✓ {file_info['name']}: {file_info['chunks']} chunks ({file_info['processing_time_seconds']}s)")

    # Verify chunk quality
    print("\n" + "="*60)
    print("VERIFYING CHUNK QUALITY")
    print("="*60)
    verification = pipeline.verify_chunk_quality()

    print(f"\nCollection: {verification['collection_stats']['name']}")
    print(f"Total chunks stored: {verification['collection_stats']['count']}")

    print("\nSample retrieval tests:")
    for result in verification['sample_retrievals']:
        if 'error' in result:
            print(f"  ❌ '{result['query']}': ERROR")
        else:
            print(f"  ✓ '{result['query']}': {result['results_count']} results")
            if result.get('top_result_preview'):
                print(f"    Preview: {result['top_result_preview'][:100]}...")

    print("\n" + "="*60)
    print("PROCESSING COMPLETE")
    print("="*60)
    print(f"Processed chunks saved to: {settings.processed_dir}")
    print(f"ChromaDB persist directory: {settings.chroma_persist_dir}")


if __name__ == "__main__":
    main()
