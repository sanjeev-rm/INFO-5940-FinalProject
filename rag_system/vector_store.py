"""
Vector Store

Manages vector storage and similarity search using ChromaDB.
"""

import logging
import chromadb
from typing import List, Dict, Any, Optional
from pathlib import Path
import json

from config.settings import AppConfig

class VectorStore:
    """ChromaDB-based vector store for document embeddings"""

    def __init__(self, config: AppConfig):
        """
        Initialize vector store

        Args:
            config: Application configuration
        """
        self.config = config
        self.logger = logging.getLogger(__name__)

        # Initialize ChromaDB client
        self.client = chromadb.PersistentClient(path=config.CHROMA_PERSIST_DIR)

        # Get or create collection
        self.collection = self._get_or_create_collection()

    def _get_or_create_collection(self):
        """Get existing collection or create new one"""
        try:
            # Try to get existing collection
            collection = self.client.get_collection(name=self.config.CHROMA_COLLECTION_NAME)
            self.logger.info(f"Loaded existing collection: {self.config.CHROMA_COLLECTION_NAME}")
            return collection

        except ValueError:
            # Collection doesn't exist, create new one
            self.logger.info(f"Creating new collection: {self.config.CHROMA_COLLECTION_NAME}")

            collection = self.client.create_collection(
                name=self.config.CHROMA_COLLECTION_NAME,
                metadata={"description": "Hotel training documents collection"}
            )
            return collection

    def add_document(self, content: str, embedding: List[float],
                    metadata: Dict[str, Any], document_id: Optional[str] = None) -> str:
        """
        Add a document to the vector store

        Args:
            content: Document content text
            embedding: Document embedding vector
            metadata: Document metadata
            document_id: Optional custom document ID

        Returns:
            str: Document ID
        """
        try:
            # Generate document ID if not provided
            if not document_id:
                import hashlib
                document_id = hashlib.md5(content.encode()).hexdigest()[:16]

            # Prepare metadata (ChromaDB requires string values)
            chroma_metadata = {}
            for key, value in metadata.items():
                if isinstance(value, (str, int, float, bool)):
                    chroma_metadata[key] = str(value)
                else:
                    chroma_metadata[key] = json.dumps(value)

            # Add document to collection
            self.collection.add(
                embeddings=[embedding],
                documents=[content],
                metadatas=[chroma_metadata],
                ids=[document_id]
            )

            self.logger.debug(f"Added document {document_id} to vector store")
            return document_id

        except Exception as e:
            self.logger.error(f"Failed to add document to vector store: {e}")
            raise Exception(f"Vector store add error: {e}")

    def search_similar(self, query_embedding: List[float], top_k: int = 5,
                      similarity_threshold: float = 0.0) -> List[Dict[str, Any]]:
        """
        Search for similar documents

        Args:
            query_embedding: Query embedding vector
            top_k: Number of top results to return
            similarity_threshold: Minimum similarity score

        Returns:
            List of similar documents with metadata and scores
        """
        try:
            # Query the collection
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k
            )

            # Process and format results
            formatted_results = []

            if results["documents"] and len(results["documents"]) > 0:
                documents = results["documents"][0]
                metadatas = results["metadatas"][0] if results["metadatas"] else [{}] * len(documents)
                distances = results["distances"][0] if results["distances"] else [0.0] * len(documents)
                ids = results["ids"][0] if results["ids"] else [""] * len(documents)

                for i, (doc, metadata, distance, doc_id) in enumerate(zip(documents, metadatas, distances, ids)):
                    # Convert distance to similarity score (ChromaDB uses L2 distance)
                    similarity_score = 1.0 / (1.0 + distance)

                    # Filter by similarity threshold
                    if similarity_score >= similarity_threshold:
                        # Parse metadata back from strings
                        parsed_metadata = self._parse_metadata(metadata)

                        formatted_results.append({
                            "id": doc_id,
                            "content": doc,
                            "metadata": parsed_metadata,
                            "similarity_score": similarity_score,
                            "distance": distance
                        })

            # Sort by similarity score (highest first)
            formatted_results.sort(key=lambda x: x["similarity_score"], reverse=True)

            self.logger.debug(f"Retrieved {len(formatted_results)} similar documents")
            return formatted_results

        except Exception as e:
            self.logger.error(f"Failed to search vector store: {e}")
            return []

    def _parse_metadata(self, metadata: Dict[str, str]) -> Dict[str, Any]:
        """
        Parse metadata from ChromaDB string format back to original types

        Args:
            metadata: Metadata dictionary with string values

        Returns:
            Dict with parsed values
        """
        parsed = {}
        for key, value in metadata.items():
            try:
                # Try to parse as JSON first (for complex types)
                if value.startswith(('[', '{')):
                    parsed[key] = json.loads(value)
                # Try to parse as number
                elif value.replace('.', '', 1).replace('-', '', 1).isdigit():
                    parsed[key] = float(value) if '.' in value else int(value)
                # Try to parse as boolean
                elif value.lower() in ('true', 'false'):
                    parsed[key] = value.lower() == 'true'
                # Keep as string
                else:
                    parsed[key] = value
            except (json.JSONDecodeError, ValueError):
                # If parsing fails, keep as string
                parsed[key] = value

        return parsed

    def get_document_by_id(self, document_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a document by its ID

        Args:
            document_id: Document identifier

        Returns:
            Document data or None if not found
        """
        try:
            results = self.collection.get(ids=[document_id])

            if results["documents"] and len(results["documents"]) > 0:
                return {
                    "id": document_id,
                    "content": results["documents"][0],
                    "metadata": self._parse_metadata(results["metadatas"][0]) if results["metadatas"] else {}
                }
            else:
                return None

        except Exception as e:
            self.logger.error(f"Failed to get document {document_id}: {e}")
            return None

    def update_document(self, document_id: str, content: str = None,
                       embedding: List[float] = None, metadata: Dict[str, Any] = None) -> bool:
        """
        Update an existing document

        Args:
            document_id: Document identifier
            content: New content (optional)
            embedding: New embedding (optional)
            metadata: New metadata (optional)

        Returns:
            bool: Success status
        """
        try:
            update_data = {}

            if content is not None:
                update_data["documents"] = [content]

            if embedding is not None:
                update_data["embeddings"] = [embedding]

            if metadata is not None:
                # Convert metadata to ChromaDB format
                chroma_metadata = {}
                for key, value in metadata.items():
                    if isinstance(value, (str, int, float, bool)):
                        chroma_metadata[key] = str(value)
                    else:
                        chroma_metadata[key] = json.dumps(value)
                update_data["metadatas"] = [chroma_metadata]

            if update_data:
                update_data["ids"] = [document_id]
                self.collection.update(**update_data)
                self.logger.debug(f"Updated document {document_id}")
                return True
            else:
                self.logger.warning("No update data provided")
                return False

        except Exception as e:
            self.logger.error(f"Failed to update document {document_id}: {e}")
            return False

    def delete_document(self, document_id: str) -> bool:
        """
        Delete a document from the vector store

        Args:
            document_id: Document identifier

        Returns:
            bool: Success status
        """
        try:
            self.collection.delete(ids=[document_id])
            self.logger.debug(f"Deleted document {document_id}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to delete document {document_id}: {e}")
            return False

    def get_collection_info(self) -> Dict[str, Any]:
        """
        Get information about the collection

        Returns:
            Dict containing collection statistics
        """
        try:
            count = self.collection.count()
            return {
                "name": self.config.CHROMA_COLLECTION_NAME,
                "document_count": count,
                "persist_directory": self.config.CHROMA_PERSIST_DIR
            }

        except Exception as e:
            self.logger.error(f"Failed to get collection info: {e}")
            return {"error": str(e)}

    def clear_collection(self) -> bool:
        """
        Clear all documents from the collection

        Returns:
            bool: Success status
        """
        try:
            # Get all document IDs
            results = self.collection.get()
            if results["ids"]:
                self.collection.delete(ids=results["ids"])

            self.logger.info("Cleared collection")
            return True

        except Exception as e:
            self.logger.error(f"Failed to clear collection: {e}")
            return False

    def backup_collection(self, backup_path: str) -> bool:
        """
        Create a backup of the collection

        Args:
            backup_path: Path to save backup

        Returns:
            bool: Success status
        """
        try:
            # Get all data from collection
            results = self.collection.get()

            backup_data = {
                "collection_name": self.config.CHROMA_COLLECTION_NAME,
                "documents": results["documents"],
                "metadatas": results["metadatas"],
                "ids": results["ids"],
                "created_at": str(self.config.get_current_timestamp())
            }

            # Save to file
            backup_file = Path(backup_path)
            backup_file.parent.mkdir(parents=True, exist_ok=True)

            with open(backup_file, 'w', encoding='utf-8') as f:
                json.dump(backup_data, f, indent=2)

            self.logger.info(f"Collection backed up to {backup_path}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to backup collection: {e}")
            return False