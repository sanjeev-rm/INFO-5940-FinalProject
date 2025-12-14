"""
Text Chunker

Handles intelligent text chunking for optimal embedding and retrieval.
"""

import logging
import re
from typing import List
from config.settings import AppConfig

class TextChunker:
    """Intelligent text chunking for document processing"""

    def __init__(self, config: AppConfig):
        """
        Initialize text chunker

        Args:
            config: Application configuration
        """
        self.config = config
        self.logger = logging.getLogger(__name__)

        self.chunk_size = config.CHUNK_SIZE
        self.chunk_overlap = config.CHUNK_OVERLAP

    def chunk_text(self, text: str, chunk_method: str = "recursive") -> List[str]:
        """
        Split text into chunks using the specified method

        Args:
            text: Input text to chunk
            chunk_method: Chunking method ("recursive", "sentence", "paragraph")

        Returns:
            List of text chunks
        """
        if not text.strip():
            return []

        # Clean the text first
        cleaned_text = self._clean_text(text)

        # Choose chunking method
        if chunk_method == "sentence":
            return self._chunk_by_sentences(cleaned_text)
        elif chunk_method == "paragraph":
            return self._chunk_by_paragraphs(cleaned_text)
        else:  # recursive (default)
            return self._chunk_recursively(cleaned_text)

    def _clean_text(self, text: str) -> str:
        """
        Clean text by removing excessive whitespace and normalizing

        Args:
            text: Input text

        Returns:
            Cleaned text
        """
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)

        # Remove excessive newlines but preserve paragraph breaks
        text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)

        # Strip leading/trailing whitespace
        text = text.strip()

        return text

    def _chunk_recursively(self, text: str) -> List[str]:
        """
        Chunk text recursively, trying to preserve semantic boundaries

        Args:
            text: Input text

        Returns:
            List of text chunks
        """
        if len(text) <= self.chunk_size:
            return [text] if text.strip() else []

        chunks = []

        # Define separators in order of preference (most semantic to least)
        separators = [
            '\n\n',  # Paragraph breaks
            '\n',    # Line breaks
            '. ',    # Sentence endings
            '! ',    # Exclamation sentences
            '? ',    # Question sentences
            '; ',    # Semicolon breaks
            ', ',    # Comma breaks
            ' ',     # Word breaks
        ]

        # Try to split using the best available separator
        for separator in separators:
            if separator in text:
                chunks = self._split_by_separator(text, separator)
                if chunks:  # Successfully chunked
                    break

        # If no separator worked, fall back to character-based chunking
        if not chunks:
            chunks = self._chunk_by_characters(text)

        return [chunk.strip() for chunk in chunks if chunk.strip()]

    def _split_by_separator(self, text: str, separator: str) -> List[str]:
        """
        Split text by separator while respecting chunk size limits

        Args:
            text: Input text
            separator: Separator to split on

        Returns:
            List of chunks or empty list if splitting wasn't effective
        """
        parts = text.split(separator)
        chunks = []
        current_chunk = ""

        for part in parts:
            # Reconstruct with separator (except for the first part)
            if current_chunk:
                test_chunk = current_chunk + separator + part
            else:
                test_chunk = part

            if len(test_chunk) <= self.chunk_size:
                current_chunk = test_chunk
            else:
                # Current chunk is full, start a new one
                if current_chunk:
                    chunks.append(current_chunk)

                # If single part is too large, recursively chunk it
                if len(part) > self.chunk_size:
                    sub_chunks = self._chunk_recursively(part)
                    chunks.extend(sub_chunks)
                    current_chunk = ""
                else:
                    current_chunk = part

        # Add the last chunk
        if current_chunk:
            chunks.append(current_chunk)

        # Apply overlap if we have multiple chunks
        if len(chunks) > 1:
            chunks = self._apply_overlap(chunks)

        return chunks

    def _chunk_by_sentences(self, text: str) -> List[str]:
        """
        Chunk text by sentences, respecting chunk size limits

        Args:
            text: Input text

        Returns:
            List of sentence-based chunks
        """
        # Split into sentences using a more sophisticated pattern
        sentence_pattern = r'(?<=[.!?])\s+'
        sentences = re.split(sentence_pattern, text)

        chunks = []
        current_chunk = ""

        for sentence in sentences:
            test_chunk = current_chunk + " " + sentence if current_chunk else sentence

            if len(test_chunk) <= self.chunk_size:
                current_chunk = test_chunk
            else:
                # Add current chunk and start new one
                if current_chunk:
                    chunks.append(current_chunk)

                # If single sentence is too long, split it further
                if len(sentence) > self.chunk_size:
                    sub_chunks = self._chunk_recursively(sentence)
                    chunks.extend(sub_chunks)
                    current_chunk = ""
                else:
                    current_chunk = sentence

        if current_chunk:
            chunks.append(current_chunk)

        return self._apply_overlap(chunks) if len(chunks) > 1 else chunks

    def _chunk_by_paragraphs(self, text: str) -> List[str]:
        """
        Chunk text by paragraphs, splitting large paragraphs if needed

        Args:
            text: Input text

        Returns:
            List of paragraph-based chunks
        """
        paragraphs = text.split('\n\n')
        chunks = []

        for paragraph in paragraphs:
            paragraph = paragraph.strip()
            if not paragraph:
                continue

            if len(paragraph) <= self.chunk_size:
                chunks.append(paragraph)
            else:
                # Paragraph is too large, split it further
                sub_chunks = self._chunk_recursively(paragraph)
                chunks.extend(sub_chunks)

        return self._apply_overlap(chunks) if len(chunks) > 1 else chunks

    def _chunk_by_characters(self, text: str) -> List[str]:
        """
        Fallback method: chunk by character count with word boundaries

        Args:
            text: Input text

        Returns:
            List of character-based chunks
        """
        chunks = []
        start = 0

        while start < len(text):
            end = start + self.chunk_size

            # If we're at the end, take everything
            if end >= len(text):
                chunks.append(text[start:])
                break

            # Try to find a word boundary near the end
            chunk_end = end
            while chunk_end > start and text[chunk_end] != ' ':
                chunk_end -= 1

            # If we couldn't find a space, just cut at character limit
            if chunk_end == start:
                chunk_end = end

            chunk = text[start:chunk_end]
            chunks.append(chunk)

            start = chunk_end - self.chunk_overlap

        return chunks

    def _apply_overlap(self, chunks: List[str]) -> List[str]:
        """
        Apply overlap between chunks to maintain context

        Args:
            chunks: List of chunks to add overlap to

        Returns:
            List of chunks with overlap applied
        """
        if len(chunks) <= 1 or self.chunk_overlap <= 0:
            return chunks

        overlapped_chunks = [chunks[0]]  # First chunk stays the same

        for i in range(1, len(chunks)):
            current_chunk = chunks[i]
            previous_chunk = chunks[i - 1]

            # Get overlap text from the end of previous chunk
            overlap_text = self._get_overlap_text(previous_chunk, self.chunk_overlap)

            # Combine overlap with current chunk
            if overlap_text:
                overlapped_chunk = overlap_text + " " + current_chunk
            else:
                overlapped_chunk = current_chunk

            overlapped_chunks.append(overlapped_chunk)

        return overlapped_chunks

    def _get_overlap_text(self, text: str, overlap_size: int) -> str:
        """
        Extract overlap text from the end of a chunk, preserving word boundaries

        Args:
            text: Source text
            overlap_size: Number of characters to overlap

        Returns:
            Overlap text
        """
        if len(text) <= overlap_size:
            return text

        # Start from the desired overlap position
        start_pos = len(text) - overlap_size

        # Find the next word boundary
        while start_pos < len(text) and text[start_pos] != ' ':
            start_pos += 1

        # If we found a space, start after it
        if start_pos < len(text):
            start_pos += 1

        return text[start_pos:].strip()

    def get_chunk_info(self, text: str) -> dict:
        """
        Get information about how text would be chunked

        Args:
            text: Input text

        Returns:
            Dictionary with chunking information
        """
        chunks = self.chunk_text(text)

        chunk_sizes = [len(chunk) for chunk in chunks]

        return {
            "original_length": len(text),
            "chunk_count": len(chunks),
            "average_chunk_size": sum(chunk_sizes) / len(chunk_sizes) if chunk_sizes else 0,
            "min_chunk_size": min(chunk_sizes) if chunk_sizes else 0,
            "max_chunk_size": max(chunk_sizes) if chunk_sizes else 0,
            "chunk_size_limit": self.chunk_size,
            "overlap_size": self.chunk_overlap
        }