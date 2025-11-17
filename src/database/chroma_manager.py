"""ChromaDB manager for vector storage and retrieval."""

from typing import List, Dict, Any, Optional
import uuid

import chromadb
from chromadb.config import Settings
import google.generativeai as genai

from ..utils.config import settings
from ..utils.logging_config import get_logger

logger = get_logger(__name__)


class ChromaManager:
    """Manager for ChromaDB operations."""

    def __init__(self, persist_directory: Optional[str] = None):
        """Initialize ChromaDB client."""
        self.persist_directory = persist_directory or settings.chroma_persist_dir

        # Initialize ChromaDB client with persistence
        self.client = chromadb.Client(
            Settings(
                persist_directory=self.persist_directory,
                anonymized_telemetry=False,
            )
        )

        # Configure Gemini for embeddings
        genai.configure(api_key=settings.gemini_api_key)

        logger.info("ChromaDB manager initialized", persist_dir=self.persist_directory)

    def _generate_embedding(self, text: str) -> List[float]:
        """Generate embedding using Gemini."""
        try:
            result = genai.embed_content(
                model=settings.embedding_model,
                content=text,
                task_type="retrieval_document",
            )
            return result['embedding']
        except Exception as e:
            logger.error("Error generating embedding", error=str(e), text_preview=text[:100])
            raise

    def _generate_query_embedding(self, text: str) -> List[float]:
        """Generate embedding for query using Gemini."""
        try:
            result = genai.embed_content(
                model=settings.embedding_model,
                content=text,
                task_type="retrieval_query",
            )
            return result['embedding']
        except Exception as e:
            logger.error("Error generating query embedding", error=str(e), text=text)
            raise

    def create_collection(
        self, collection_name: str, metadata: Optional[Dict[str, Any]] = None
    ) -> chromadb.Collection:
        """Create or get a collection."""
        try:
            # ChromaDB requires metadata to be None or a non-empty dict
            collection_metadata = metadata if metadata else {"created": "true"}

            collection = self.client.get_or_create_collection(
                name=collection_name,
                metadata=collection_metadata,
            )
            logger.info("Collection created/retrieved", name=collection_name)
            return collection
        except Exception as e:
            logger.error("Error creating collection", error=str(e), name=collection_name)
            raise

    def add_documents(
        self,
        collection_name: str,
        documents: List[str],
        metadatas: List[Dict[str, Any]],
        ids: Optional[List[str]] = None,
    ) -> None:
        """Add documents to a collection with embeddings."""
        try:
            collection = self.client.get_collection(collection_name)

            # Generate IDs if not provided
            if ids is None:
                ids = [str(uuid.uuid4()) for _ in documents]

            # Generate embeddings
            logger.info("Generating embeddings", count=len(documents))
            embeddings = [self._generate_embedding(doc) for doc in documents]

            # Add to collection
            collection.add(
                documents=documents,
                embeddings=embeddings,
                metadatas=metadatas,
                ids=ids,
            )

            logger.info(
                "Documents added to collection",
                collection=collection_name,
                count=len(documents),
            )
        except Exception as e:
            logger.error(
                "Error adding documents",
                error=str(e),
                collection=collection_name,
                count=len(documents),
            )
            raise

    def query(
        self,
        collection_name: str,
        query_text: str,
        n_results: int = 5,
        where: Optional[Dict[str, Any]] = None,
        where_document: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Query a collection using semantic search."""
        try:
            collection = self.client.get_collection(collection_name)

            # Generate query embedding
            query_embedding = self._generate_query_embedding(query_text)

            # Query collection
            results = collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results,
                where=where,
                where_document=where_document,
            )

            logger.info(
                "Query executed",
                collection=collection_name,
                query_preview=query_text[:50],
                n_results=n_results,
                results_count=len(results['ids'][0]) if results['ids'] else 0,
            )

            return results
        except Exception as e:
            logger.error(
                "Error querying collection",
                error=str(e),
                collection=collection_name,
                query=query_text,
            )
            raise

    def hybrid_search(
        self,
        collection_name: str,
        query_text: str,
        metadata_filters: Optional[Dict[str, Any]] = None,
        n_results: int = 5,
    ) -> List[Dict[str, Any]]:
        """
        Perform hybrid search combining semantic search with metadata filtering.

        Args:
            collection_name: Name of the collection to search
            query_text: Query text for semantic search
            metadata_filters: Metadata filters (e.g., {"chapter": 3, "chunk_type": "theorem"})
            n_results: Number of results to return

        Returns:
            List of search results with documents, metadata, and distances
        """
        try:
            results = self.query(
                collection_name=collection_name,
                query_text=query_text,
                n_results=n_results,
                where=metadata_filters,
            )

            # Format results
            formatted_results = []
            if results['ids'] and len(results['ids'][0]) > 0:
                for i in range(len(results['ids'][0])):
                    formatted_results.append({
                        'id': results['ids'][0][i],
                        'document': results['documents'][0][i],
                        'metadata': results['metadatas'][0][i],
                        'distance': results['distances'][0][i] if 'distances' in results else None,
                    })

            logger.info(
                "Hybrid search completed",
                collection=collection_name,
                query_preview=query_text[:50],
                filters=metadata_filters,
                results_count=len(formatted_results),
            )

            return formatted_results
        except Exception as e:
            logger.error(
                "Error in hybrid search",
                error=str(e),
                collection=collection_name,
                query=query_text,
            )
            raise

    def get_collection_stats(self, collection_name: str) -> Dict[str, Any]:
        """Get statistics about a collection."""
        try:
            collection = self.client.get_collection(collection_name)
            count = collection.count()

            logger.info("Collection stats retrieved", collection=collection_name, count=count)

            return {
                'name': collection_name,
                'count': count,
                'metadata': collection.metadata,
            }
        except Exception as e:
            logger.error("Error getting collection stats", error=str(e), collection=collection_name)
            raise

    def delete_collection(self, collection_name: str) -> None:
        """Delete a collection."""
        try:
            self.client.delete_collection(collection_name)
            logger.info("Collection deleted", collection=collection_name)
        except Exception as e:
            logger.error("Error deleting collection", error=str(e), collection=collection_name)
            raise

    def initialize_collections(self) -> None:
        """Initialize required collections for the learning companion."""
        collections = [
            {
                'name': 'textbook_chunks',
                'metadata': {
                    'description': 'Kleinberg-Tardos textbook chunks',
                    'chunk_strategy': 'fixed_size',
                    'chunk_size': settings.chunk_size,
                    'chunk_overlap': settings.chunk_overlap,
                },
            },
            {
                'name': 'lecture_notes',
                'metadata': {
                    'description': 'MIT 6.006 lecture notes',
                    'chunk_strategy': 'hierarchical',
                },
            },
            {
                'name': 'prerequisite_concepts',
                'metadata': {
                    'description': 'Prerequisite concepts for curriculum planning',
                },
            },
        ]

        for collection_config in collections:
            self.create_collection(
                collection_name=collection_config['name'],
                metadata=collection_config['metadata'],
            )

        logger.info("All collections initialized", count=len(collections))


# Global ChromaDB manager instance
_chroma_manager: Optional[ChromaManager] = None


def get_chroma_manager() -> ChromaManager:
    """Get or create ChromaDB manager instance."""
    global _chroma_manager
    if _chroma_manager is None:
        _chroma_manager = ChromaManager()
    return _chroma_manager
