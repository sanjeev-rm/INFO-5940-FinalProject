"""
RAG Retriever

Main interface for retrieving relevant training documents using vector similarity search.
"""

import logging
from typing import List, Dict, Any, Optional
from pathlib import Path

from .vector_store import VectorStore
from .embeddings import EmbeddingGenerator
from config.settings import AppConfig

class RAGRetriever:
    """Main RAG system for retrieving relevant training documents"""

    def __init__(self, config: AppConfig):
        """
        Initialize RAG retriever

        Args:
            config: Application configuration
        """
        self.config = config
        self.logger = logging.getLogger(__name__)

        # Initialize components
        self.embedding_generator = EmbeddingGenerator(config)
        self.vector_store = VectorStore(config)

        # Check if vector store needs initialization
        self._initialize_if_needed()

    def _initialize_if_needed(self) -> None:
        """Initialize vector store if it's empty or doesn't exist"""
        try:
            # Check if collection exists and has documents
            collection_info = self.vector_store.get_collection_info()

            if collection_info.get("document_count", 0) == 0:
                self.logger.info("Vector store is empty. Initializing with training documents...")
                self._initialize_vector_store()
            else:
                self.logger.info(f"Vector store loaded with {collection_info['document_count']} documents")

        except Exception as e:
            self.logger.warning(f"Could not check vector store status: {e}")
            self.logger.info("Attempting to initialize vector store...")
            self._initialize_vector_store()

    def _initialize_vector_store(self) -> None:
        """Initialize vector store with training documents"""
        try:
            # Import document processor here to avoid circular imports
            from document_processor.processor import DocumentProcessor

            doc_processor = DocumentProcessor(self.config)

            # Process all training documents
            documents = doc_processor.process_all_documents(self.config.TRAINING_DOCS_PATH)

            if documents:
                self.logger.info(f"Processing {len(documents)} documents for vector store...")

                # Generate embeddings and store documents
                for doc in documents:
                    try:
                        embedding = self.embedding_generator.generate_embedding(doc["content"])
                        self.vector_store.add_document(
                            content=doc["content"],
                            embedding=embedding,
                            metadata=doc["metadata"]
                        )
                    except Exception as e:
                        self.logger.error(f"Failed to process document {doc.get('source', 'unknown')}: {e}")

                self.logger.info("Vector store initialization completed")
            else:
                self.logger.warning("No documents found for processing")

        except ImportError as e:
            self.logger.error(f"Document processor not available: {e}")
        except Exception as e:
            self.logger.error(f"Failed to initialize vector store: {e}")

    def retrieve_relevant_content(self, query: str, top_k: int = None,
                                similarity_threshold: float = None) -> List[Dict[str, Any]]:
        """
        Retrieve relevant training documents for a query

        Args:
            query: Search query
            top_k: Number of top results to return
            similarity_threshold: Minimum similarity score

        Returns:
            List of relevant documents with content and metadata
        """
        if not query.strip():
            self.logger.warning("Empty query provided to retrieve_relevant_content")
            return []

        try:
            # Use config defaults if not provided
            top_k = top_k or self.config.RAG_TOP_K
            similarity_threshold = similarity_threshold or self.config.RAG_SIMILARITY_THRESHOLD

            # Generate query embedding
            query_embedding = self.embedding_generator.generate_embedding(query)

            # Search vector store
            results = self.vector_store.search_similar(
                query_embedding=query_embedding,
                top_k=top_k,
                similarity_threshold=similarity_threshold
            )

            # Format results
            formatted_results = []
            for result in results:
                formatted_results.append({
                    "content": result["content"],
                    "metadata": result["metadata"],
                    "similarity_score": result["similarity_score"],
                    "source": result["metadata"].get("source", "unknown")
                })

            self.logger.info(f"Retrieved {len(formatted_results)} relevant documents for query")
            return formatted_results

        except Exception as e:
            self.logger.error(f"Failed to retrieve relevant content: {e}")
            return []

    def add_new_document(self, content: str, metadata: Dict[str, Any]) -> bool:
        """
        Add a new document to the vector store

        Args:
            content: Document content
            metadata: Document metadata

        Returns:
            bool: Success status
        """
        try:
            # Generate embedding
            embedding = self.embedding_generator.generate_embedding(content)

            # Add to vector store
            self.vector_store.add_document(
                content=content,
                embedding=embedding,
                metadata=metadata
            )

            self.logger.info(f"Added new document: {metadata.get('source', 'unknown')}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to add new document: {e}")
            return False

    def search_by_keywords(self, keywords: List[str], top_k: int = None) -> List[Dict[str, Any]]:
        """
        Search for documents containing specific keywords

        Args:
            keywords: List of keywords to search for
            top_k: Number of results to return

        Returns:
            List of matching documents
        """
        if not keywords:
            return []

        # Create query from keywords
        query = " ".join(keywords)
        return self.retrieve_relevant_content(query, top_k)

    def get_document_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the document collection

        Returns:
            Dict containing collection statistics
        """
        try:
            stats = self.vector_store.get_collection_info()
            return {
                "total_documents": stats.get("document_count", 0),
                "collection_name": self.config.CHROMA_COLLECTION_NAME,
                "embedding_model": self.config.EMBEDDING_MODEL,
                "chunk_size": self.config.CHUNK_SIZE,
                "chunk_overlap": self.config.CHUNK_OVERLAP
            }
        except Exception as e:
            self.logger.error(f"Failed to get document stats: {e}")
            return {"error": str(e)}

    def refresh_vector_store(self) -> bool:
        """
        Refresh the vector store by reprocessing all training documents

        Returns:
            bool: Success status
        """
        try:
            self.logger.info("Refreshing vector store...")

            # Clear existing data
            self.vector_store.clear_collection()

            # Reinitialize
            self._initialize_vector_store()

            self.logger.info("Vector store refresh completed")
            return True

        except Exception as e:
            self.logger.error(f"Failed to refresh vector store: {e}")
            return False

    def identify_content_gaps(self, recent_queries: List[str]) -> Dict[str, Any]:
        """
        Identify potential gaps in training content based on queries that return few results

        Args:
            recent_queries: List of recent search queries

        Returns:
            Dict containing gap analysis
        """
        gaps = []
        low_result_queries = []

        for query in recent_queries:
            results = self.retrieve_relevant_content(query, top_k=3)

            if len(results) < 2:  # Fewer than 2 relevant results
                low_result_queries.append({
                    "query": query,
                    "result_count": len(results),
                    "best_score": results[0]["similarity_score"] if results else 0.0
                })

        return {
            "potential_gaps": low_result_queries,
            "gap_count": len(low_result_queries),
            "total_queries_analyzed": len(recent_queries),
            "recommendations": self._generate_gap_recommendations(low_result_queries)
        }

    def _generate_gap_recommendations(self, low_result_queries: List[Dict]) -> List[str]:
        """Generate recommendations for addressing content gaps"""
        if not low_result_queries:
            return ["No significant content gaps identified"]

        recommendations = []
        common_terms = {}

        # Analyze common terms in low-result queries
        for query_info in low_result_queries:
            words = query_info["query"].lower().split()
            for word in words:
                if len(word) > 3:  # Skip short words
                    common_terms[word] = common_terms.get(word, 0) + 1

        # Generate recommendations based on common terms
        frequent_terms = sorted(common_terms.items(), key=lambda x: x[1], reverse=True)[:5]

        for term, count in frequent_terms:
            recommendations.append(f"Consider adding training content about '{term}' (mentioned in {count} low-result queries)")

        return recommendations