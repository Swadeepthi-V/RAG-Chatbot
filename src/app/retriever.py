import os
import logging
import chromadb
from typing import List, Dict, Optional
from embeddings import EmbeddingService

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

class SemanticRetriever:
    """Retrieves grounded document passages from the Chroma DB collection using BGE Small embeddings."""
    def __init__(self, index_dir: str, model_name: str = "BAAI/bge-small-en-v1.5"):
        self.chroma_dir = os.path.abspath(os.path.join(index_dir, "chroma_db"))
        logger.info(f"Initializing SemanticRetriever using Chroma DB path: {self.chroma_dir}")
        
        # Load persistent client
        self.client = chromadb.PersistentClient(path=self.chroma_dir)
        self.collection = self.client.get_collection(name="hdfc_mutual_funds")
        
        # Initialize embedding service
        self.embed_service = EmbeddingService(model_name=model_name)
        
    def retrieve(self, query: str, top_k: int = 3, filter_dict: Optional[Dict] = None) -> List[Dict]:
        """Perform semantic search, returning matching passages with metadata and confidence scores."""
        # 1. Generate normalized query embedding with instruction prefix
        query_vector = self.embed_service.embed_query(query)
        
        # 2. Query collection
        # Chroma expects embeddings as a list of lists of floats
        query_results = self.collection.query(
            query_embeddings=[query_vector.tolist()],
            n_results=top_k,
            where=filter_dict
        )
        
        # 3. Parse matches
        # Chroma returns structure: {'ids': [...], 'distances': [...], 'metadatas': [...], 'documents': [...]}
        retrieved_items = []
        
        ids = query_results.get("ids", [[]])[0]
        distances = query_results.get("distances", [[]])[0]
        metadatas = query_results.get("metadatas", [[]])[0]
        documents = query_results.get("documents", [[]])[0]
        
        for idx in range(len(ids)):
            distance = distances[idx]
            # Since distance space is 'cosine', distance = 1 - cosine_similarity.
            # Thus, similarity (confidence score) = 1 - distance.
            confidence_score = 1.0 - distance
            
            retrieved_items.append({
                "id": ids[idx],
                "text": documents[idx],
                "confidence": float(confidence_score),
                "metadata": metadatas[idx]
            })
            
        logger.info(f"Retrieved {len(retrieved_items)} chunks for query: '{query}'")
        return retrieved_items

if __name__ == "__main__":
    # Local CLI testing run
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    data_dir = os.path.join(base_dir, "data")
    
    retriever = SemanticRetriever(index_dir=data_dir)
    results = retriever.retrieve("HDFC Small Cap exit load", top_k=2)
    
    for idx, match in enumerate(results):
        print(f"\n--- Match {idx + 1} (Confidence: {match['confidence']:.4f}) ---")
        print(f"Source URL: {match['metadata']['source_url']}")
        print(f"Content:\n{match['text']}")
