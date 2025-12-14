"""
Document Processor

Main class for processing various document formats and preparing them
for vectorization in the RAG system.
"""

import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
import hashlib

from .readers import DocumentReader
from .chunker import TextChunker
from config.settings import AppConfig

class DocumentProcessor:
    """Main document processing orchestrator"""

    def __init__(self, config: AppConfig):
        """
        Initialize document processor

        Args:
            config: Application configuration
        """
        self.config = config
        self.logger = logging.getLogger(__name__)

        # Initialize components
        self.reader = DocumentReader(config)
        self.chunker = TextChunker(config)

        # Track processed documents to avoid duplicates
        self.processed_documents = set()

    def process_all_documents(self, directory_path: Path) -> List[Dict[str, Any]]:
        """
        Process all documents in a directory

        Args:
            directory_path: Path to directory containing documents

        Returns:
            List of processed document chunks with metadata
        """
        if not directory_path.exists():
            self.logger.error(f"Directory does not exist: {directory_path}")
            return []

        self.logger.info(f"Processing documents in: {directory_path}")

        all_documents = []
        processed_count = 0
        error_count = 0

        # Find all supported document files
        document_files = self._find_document_files(directory_path)

        if not document_files:
            self.logger.warning(f"No supported documents found in {directory_path}")
            return []

        self.logger.info(f"Found {len(document_files)} documents to process")

        # Process each document
        for file_path in document_files:
            try:
                self.logger.debug(f"Processing: {file_path}")

                # Check if already processed (based on file hash)
                file_hash = self._calculate_file_hash(file_path)
                if file_hash in self.processed_documents:
                    self.logger.debug(f"Skipping already processed document: {file_path.name}")
                    continue

                # Process the document
                document_chunks = self.process_document(file_path)

                if document_chunks:
                    all_documents.extend(document_chunks)
                    self.processed_documents.add(file_hash)
                    processed_count += 1
                else:
                    self.logger.warning(f"No content extracted from: {file_path}")

            except Exception as e:
                self.logger.error(f"Failed to process {file_path}: {e}")
                error_count += 1

        self.logger.info(f"Document processing completed: {processed_count} successful, {error_count} errors, {len(all_documents)} total chunks")
        return all_documents

    def process_document(self, file_path: Path) -> List[Dict[str, Any]]:
        """
        Process a single document

        Args:
            file_path: Path to the document file

        Returns:
            List of document chunks with metadata
        """
        try:
            # Extract text content
            content = self.reader.read_document(file_path)

            if not content or not content.strip():
                self.logger.warning(f"No content extracted from: {file_path}")
                return []

            # Create base metadata
            metadata = self._create_base_metadata(file_path, content)

            # Chunk the content
            chunks = self.chunker.chunk_text(content)

            # Create document objects for each chunk
            document_chunks = []
            for i, chunk in enumerate(chunks):
                if chunk.strip():  # Only include non-empty chunks
                    chunk_metadata = metadata.copy()
                    chunk_metadata.update({
                        "chunk_index": i,
                        "total_chunks": len(chunks),
                        "chunk_size": len(chunk),
                        "chunk_id": f"{metadata['file_hash']}_{i}"
                    })

                    document_chunks.append({
                        "content": chunk.strip(),
                        "metadata": chunk_metadata,
                        "source": str(file_path)
                    })

            self.logger.debug(f"Created {len(document_chunks)} chunks from {file_path.name}")
            return document_chunks

        except Exception as e:
            self.logger.error(f"Failed to process document {file_path}: {e}")
            return []

    def _find_document_files(self, directory_path: Path) -> List[Path]:
        """
        Find all supported document files in a directory

        Args:
            directory_path: Directory to search

        Returns:
            List of document file paths
        """
        document_files = []

        # Recursively find all files with supported extensions
        for extension in self.config.SUPPORTED_DOCUMENT_TYPES:
            # Handle both lowercase and uppercase extensions
            pattern = f"**/*{extension}"
            files = list(directory_path.glob(pattern))

            # Also check uppercase
            pattern_upper = f"**/*{extension.upper()}"
            files.extend(list(directory_path.glob(pattern_upper)))

            document_files.extend(files)

        # Remove duplicates and sort
        document_files = list(set(document_files))
        document_files.sort()

        # Filter out files that are too large
        filtered_files = []
        for file_path in document_files:
            try:
                file_size_mb = file_path.stat().st_size / (1024 * 1024)
                if file_size_mb <= self.config.MAX_DOCUMENT_SIZE_MB:
                    filtered_files.append(file_path)
                else:
                    self.logger.warning(f"Skipping large file ({file_size_mb:.1f}MB): {file_path}")
            except OSError as e:
                self.logger.warning(f"Could not check file size for {file_path}: {e}")

        return filtered_files

    def _create_base_metadata(self, file_path: Path, content: str) -> Dict[str, Any]:
        """
        Create base metadata for a document

        Args:
            file_path: Path to the document
            content: Document content

        Returns:
            Dictionary containing base metadata
        """
        # Calculate file hash for uniqueness
        file_hash = self._calculate_file_hash(file_path)

        # Get file stats
        file_stats = file_path.stat()

        metadata = {
            "source": str(file_path),
            "filename": file_path.name,
            "file_extension": file_path.suffix.lower(),
            "file_size_bytes": file_stats.st_size,
            "file_hash": file_hash,
            "content_length": len(content),
            "created_time": file_stats.st_ctime,
            "modified_time": file_stats.st_mtime,
            "processed_time": self.config.get_current_timestamp().timestamp(),
            "document_type": self._classify_document_type(file_path, content),
            "relative_path": str(file_path.relative_to(self.config.TRAINING_DOCS_PATH))
        }

        # Add content-based metadata
        metadata.update(self._analyze_content(content))

        return metadata

    def _calculate_file_hash(self, file_path: Path) -> str:
        """
        Calculate MD5 hash of a file

        Args:
            file_path: Path to the file

        Returns:
            str: MD5 hash
        """
        hash_md5 = hashlib.md5()
        try:
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except Exception as e:
            self.logger.warning(f"Could not calculate hash for {file_path}: {e}")
            # Fallback to path-based hash
            return hashlib.md5(str(file_path).encode()).hexdigest()

    def _classify_document_type(self, file_path: Path, content: str) -> str:
        """
        Classify the type of document based on filename and content

        Args:
            file_path: Path to the document
            content: Document content

        Returns:
            str: Document type classification
        """
        filename_lower = file_path.name.lower()
        content_lower = content.lower()

        # Check for specific document types based on filename patterns
        if any(keyword in filename_lower for keyword in ['policy', 'policies', 'procedure']):
            return "policy_document"
        elif any(keyword in filename_lower for keyword in ['training', 'guide', 'manual']):
            return "training_material"
        elif any(keyword in filename_lower for keyword in ['script', 'dialogue', 'response']):
            return "service_script"
        elif any(keyword in filename_lower for keyword in ['checklist', 'steps', 'process']):
            return "procedural_guide"
        elif any(keyword in filename_lower for keyword in ['faq', 'questions', 'answers']):
            return "faq_document"

        # Check content for classification clues
        if any(keyword in content_lower for keyword in ['greeting', 'welcome', 'hello']):
            return "greeting_guide"
        elif any(keyword in content_lower for keyword in ['complaint', 'issue', 'problem', 'recovery']):
            return "service_recovery"
        elif any(keyword in content_lower for keyword in ['billing', 'payment', 'charge', 'refund']):
            return "billing_guidance"

        # Default classification based on file extension
        extension = file_path.suffix.lower()
        if extension in ['.pdf']:
            return "pdf_document"
        elif extension in ['.doc', '.docx']:
            return "word_document"
        elif extension in ['.xlsx', '.xls']:
            return "spreadsheet"
        elif extension in ['.txt']:
            return "text_document"

        return "general_document"

    def _analyze_content(self, content: str) -> Dict[str, Any]:
        """
        Analyze content to extract additional metadata

        Args:
            content: Document content

        Returns:
            Dict containing content analysis
        """
        # Basic text statistics
        words = content.split()
        sentences = content.split('.')
        paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]

        # Identify key topics (simple keyword extraction)
        key_topics = self._extract_key_topics(content)

        return {
            "word_count": len(words),
            "sentence_count": len(sentences),
            "paragraph_count": len(paragraphs),
            "key_topics": key_topics,
            "has_contact_info": self._has_contact_info(content),
            "has_procedures": self._has_procedures(content),
            "language": "english"  # Could be enhanced with language detection
        }

    def _extract_key_topics(self, content: str) -> List[str]:
        """
        Extract key topics from content using simple keyword matching

        Args:
            content: Document content

        Returns:
            List of identified topics
        """
        content_lower = content.lower()

        # Define topic keywords
        topic_keywords = {
            "customer_service": ["customer", "service", "guest", "satisfaction"],
            "billing": ["bill", "charge", "payment", "refund", "invoice"],
            "reservations": ["reservation", "booking", "check-in", "check-out"],
            "complaints": ["complaint", "issue", "problem", "dissatisfied"],
            "amenities": ["pool", "gym", "wifi", "breakfast", "parking"],
            "room_service": ["room service", "housekeeping", "maintenance"],
            "policies": ["policy", "rule", "regulation", "guideline"],
            "emergency": ["emergency", "safety", "security", "evacuation"]
        }

        identified_topics = []
        for topic, keywords in topic_keywords.items():
            if any(keyword in content_lower for keyword in keywords):
                identified_topics.append(topic)

        return identified_topics

    def _has_contact_info(self, content: str) -> bool:
        """Check if content contains contact information"""
        import re
        # Simple patterns for email and phone
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        phone_pattern = r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b'

        return bool(re.search(email_pattern, content) or re.search(phone_pattern, content))

    def _has_procedures(self, content: str) -> bool:
        """Check if content contains procedural information"""
        procedure_indicators = [
            "step", "procedure", "process", "follow", "instructions",
            "first", "then", "next", "finally", "1.", "2.", "3."
        ]
        content_lower = content.lower()
        return any(indicator in content_lower for indicator in procedure_indicators)

    def get_processing_stats(self) -> Dict[str, Any]:
        """
        Get statistics about processed documents

        Returns:
            Dictionary containing processing statistics
        """
        return {
            "processed_files": len(self.processed_documents),
            "supported_extensions": self.config.SUPPORTED_DOCUMENT_TYPES,
            "max_file_size_mb": self.config.MAX_DOCUMENT_SIZE_MB,
            "chunk_size": self.config.CHUNK_SIZE,
            "chunk_overlap": self.config.CHUNK_OVERLAP
        }