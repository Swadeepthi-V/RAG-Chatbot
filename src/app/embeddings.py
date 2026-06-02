import os
import logging
import torch
import numpy as np
from typing import List
from sentence_transformers import SentenceTransformer

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Optimize PyTorch CPU threading configuration for memory footprint conservation
try:
    torch.set_num_threads(1)
    torch.set_num_interop_threads(1)
    logger.info("Configured PyTorch to operate single-threaded to minimize RAM usage.")
except Exception as e:
    logger.warning(f"Could not configure PyTorch thread boundaries: {e}")

class EmbeddingService:
    """CPU-optimized service for generating dense vector embeddings using BGE Small."""
    def __init__(self, model_name: str = "BAAI/bge-small-en-v1.5"):
        self.model_name = model_name
        self.model = None
        
    def load_model(self):
        """Lazy load the embedding model to control startup memory allocation."""
        if self.model is None:
            logger.info(f"Loading embedding model '{self.model_name}' on CPU...")
            # Force CPU to comply with 512MB RAM constraints and avoid CUDA driver overhead
            self.model = SentenceTransformer(self.model_name, device="cpu")
            logger.info("Embedding model loaded successfully.")
            
    def get_dimension(self) -> int:
        """Return the vector dimensionality of the embedding model."""
        self.load_model()
        return self.model.get_sentence_embedding_dimension()

    def embed_documents(self, texts: List[str]) -> np.ndarray:
        """Generate embeddings for text passages (no prefix required for BGE passages)."""
        self.load_model()
        if not texts:
            return np.empty((0, self.get_dimension()), dtype=np.float32)
            
        logger.info(f"Encoding batch of {len(texts)} chunks...")
        embeddings = self.model.encode(
            texts,
            batch_size=32,
            show_progress_bar=False,
            convert_to_numpy=True,
            normalize_embeddings=True  # Cosine similarity uses normalized L2 vectors
        )
        return embeddings.astype(np.float32)

    def embed_query(self, query: str) -> np.ndarray:
        """Generate embedding for search queries (BGE requires prefixing queries)."""
        self.load_model()
        # BGE v1.5 instruction prefix for query matching
        query_with_prefix = f"Represent this sentence for searching relevant passages: {query}"
        
        embeddings = self.model.encode(
            [query_with_prefix],
            show_progress_bar=False,
            convert_to_numpy=True,
            normalize_embeddings=True
        )
        return embeddings[0].astype(np.float32)
