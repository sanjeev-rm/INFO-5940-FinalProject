"""
Embedding Generator

Handles text embedding generation using configured embedding models.
"""

import requests
import logging
import time
from typing import List, Union
from config.settings import AppConfig

class EmbeddingGenerator:
    """Generates text embeddings using configured embedding API"""

    def __init__(self, config: AppConfig):
        """
        Initialize embedding generator

        Args:
            config: Application configuration
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.embedding_config = config.get_embedding_config()

    def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for a single text

        Args:
            text: Input text to embed

        Returns:
            List of float values representing the embedding
        """
        if not text.strip():
            raise ValueError("Cannot generate embedding for empty text")

        try:
            # Prepare API request
            payload = {
                "model": self.embedding_config["model"],
                "input": text.strip()
            }

            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.embedding_config['api_key']}"
            }

            # Make API request
            response = requests.post(
                self.embedding_config["api_url"],
                headers=headers,
                json=payload,
                timeout=30
            )

            response.raise_for_status()
            result = response.json()

            # Extract embedding from response
            if "data" in result and len(result["data"]) > 0:
                embedding = result["data"][0]["embedding"]
                return embedding
            else:
                raise ValueError("No embedding data in API response")

        except requests.exceptions.RequestException as e:
            self.logger.error(f"API request failed for embedding generation: {e}")
            raise Exception(f"Failed to generate embedding: {e}")

        except Exception as e:
            self.logger.error(f"Unexpected error in embedding generation: {e}")
            raise Exception(f"Embedding generation error: {e}")

    def generate_embeddings_batch(self, texts: List[str], batch_size: int = 100) -> List[List[float]]:
        """
        Generate embeddings for multiple texts in batches

        Args:
            texts: List of input texts
            batch_size: Number of texts to process in each batch

        Returns:
            List of embeddings corresponding to input texts
        """
        if not texts:
            return []

        embeddings = []
        total_batches = (len(texts) + batch_size - 1) // batch_size

        self.logger.info(f"Generating embeddings for {len(texts)} texts in {total_batches} batches")

        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            batch_num = (i // batch_size) + 1

            try:
                self.logger.debug(f"Processing batch {batch_num}/{total_batches}")

                # Process batch
                batch_embeddings = self._process_embedding_batch(batch)
                embeddings.extend(batch_embeddings)

                # Add small delay between batches to avoid rate limiting
                if batch_num < total_batches:
                    time.sleep(0.1)

            except Exception as e:
                self.logger.error(f"Failed to process batch {batch_num}: {e}")

                # Generate individual embeddings for failed batch
                for text in batch:
                    try:
                        embedding = self.generate_embedding(text)
                        embeddings.append(embedding)
                        time.sleep(0.05)  # Small delay between individual requests
                    except Exception as individual_error:
                        self.logger.error(f"Failed to generate individual embedding: {individual_error}")
                        # Add zero vector as fallback
                        embeddings.append([0.0] * 1536)  # Default embedding dimension

        self.logger.info(f"Generated {len(embeddings)} embeddings")
        return embeddings

    def _process_embedding_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Process a batch of texts for embedding generation

        Args:
            texts: Batch of texts to embed

        Returns:
            List of embeddings for the batch
        """
        try:
            # For OpenAI-style APIs, we can send multiple texts in one request
            payload = {
                "model": self.embedding_config["model"],
                "input": texts
            }

            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.embedding_config['api_key']}"
            }

            response = requests.post(
                self.embedding_config["api_url"],
                headers=headers,
                json=payload,
                timeout=60  # Longer timeout for batch requests
            )

            response.raise_for_status()
            result = response.json()

            # Extract embeddings from batch response
            if "data" in result:
                embeddings = []
                for item in result["data"]:
                    embeddings.append(item["embedding"])
                return embeddings
            else:
                raise ValueError("No embedding data in batch API response")

        except Exception as e:
            self.logger.warning(f"Batch processing failed: {e}. Falling back to individual requests.")
            raise e

    def get_embedding_dimension(self) -> int:
        """
        Get the dimension of embeddings generated by the current model

        Returns:
            int: Embedding dimension
        """
        # Common embedding dimensions for popular models
        model_dimensions = {
            "text-embedding-ada-002": 1536,
            "text-embedding-3-small": 1536,
            "text-embedding-3-large": 3072,
            "sentence-transformers/all-MiniLM-L6-v2": 384,
            "sentence-transformers/all-mpnet-base-v2": 768
        }

        model_name = self.embedding_config["model"]
        dimension = model_dimensions.get(model_name)

        if dimension:
            return dimension
        else:
            # Try to determine dimension by generating a test embedding
            try:
                test_embedding = self.generate_embedding("test")
                return len(test_embedding)
            except Exception as e:
                self.logger.warning(f"Could not determine embedding dimension: {e}")
                return 1536  # Default fallback

    def validate_embedding(self, embedding: List[float]) -> bool:
        """
        Validate an embedding vector

        Args:
            embedding: Embedding vector to validate

        Returns:
            bool: True if valid, False otherwise
        """
        if not isinstance(embedding, list):
            return False

        if len(embedding) == 0:
            return False

        # Check if all elements are numbers
        try:
            for val in embedding:
                float(val)
            return True
        except (ValueError, TypeError):
            return False

    def compute_similarity(self, embedding1: List[float], embedding2: List[float]) -> float:
        """
        Compute cosine similarity between two embeddings

        Args:
            embedding1: First embedding vector
            embedding2: Second embedding vector

        Returns:
            float: Cosine similarity score
        """
        if len(embedding1) != len(embedding2):
            raise ValueError("Embeddings must have the same dimension")

        # Compute dot product
        dot_product = sum(a * b for a, b in zip(embedding1, embedding2))

        # Compute magnitudes
        magnitude1 = sum(a * a for a in embedding1) ** 0.5
        magnitude2 = sum(b * b for b in embedding2) ** 0.5

        # Avoid division by zero
        if magnitude1 == 0 or magnitude2 == 0:
            return 0.0

        # Compute cosine similarity
        return dot_product / (magnitude1 * magnitude2)