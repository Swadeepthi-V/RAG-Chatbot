import os
import gc
import time
import json
import logging
import unittest
import numpy as np
import chromadb
from chunker import SimpleRecursiveSplitter, chunk_document
from embeddings import EmbeddingService
from indexer import build_index, delete_directory_with_retry
from retriever import SemanticRetriever

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

class TestIngestionPipeline(unittest.TestCase):
    def setUp(self):
        self.test_text = (
            "Exit Load\n"
            "● In respect of each purchase/switch-in of Units, an Exit Load of 1.00% is payable "
            "if Units are redeemed/switched-out within 1 year from the date of allotment.\n"
            "● No Exit Load is payable if Units are redeemed/switched-out after 1 year.\n\n"
            "Product Labelling\n"
            "This product is suitable for investors seeking long-term capital appreciation "
            "and predominantly investing in mid-cap equity instruments."
        )
        self.base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        self.test_data_dir = os.path.join(self.base_dir, "data")
        self.test_cleaned_dir = os.path.join(self.test_data_dir, "cleaned_text")
        
        # Test paths for indexer swaps (isolated to data/test_db to prevent overwriting production chroma_db)
        self.test_db_dir = os.path.join(self.test_data_dir, "test_db")
        self.test_index_path = os.path.join(self.test_db_dir, "test_vector_store.index")
        self.test_meta_path = os.path.join(self.test_db_dir, "test_vector_store.meta")
        self.test_chroma_dir = os.path.join(self.test_db_dir, "chroma_db")

    def test_recursive_splitter_boundaries(self):
        """Verify that the recursive text splitter splits on boundaries and respects chunk size constraints."""
        splitter = SimpleRecursiveSplitter(chunk_size=150, chunk_overlap=30)
        chunks = splitter.split_text(self.test_text)
        
        logger.info(f"Split test text into {len(chunks)} chunks:")
        for idx, c in enumerate(chunks):
            logger.info(f"Chunk {idx}: (Length {len(c)}) {repr(c)}")
            
        for chunk in chunks:
            # Each chunk must respect size limits
            self.assertTrue(len(chunk) <= 150, f"Chunk exceeded size limits: {len(chunk)} characters")
            
        # Verify that it splits at newlines or spaces, not arbitrarily
        # Any chunk containing the end of the first sentence must end at the clean boundary 'allotment.'
        found = False
        for c in chunks:
            if "allotment." in c:
                self.assertTrue(c.endswith("allotment."), f"Chunk did not end at sentence boundary: {repr(c)}")
                found = True
        self.assertTrue(found, "Could not find a chunk containing 'allotment.'")

    def test_chunk_document_enrichment(self):
        """Verify that scheme names are correctly prepended and total length respects constraints."""
        filename = "explore_mutual-funds_hdfc-mid-cap-fund_direct.txt"
        chunks = chunk_document(filename, self.test_text, chunk_size=384, chunk_overlap=80)
        
        self.assertTrue(len(chunks) > 0)
        for idx, chunk in enumerate(chunks):
            text = chunk["text"]
            meta = chunk["metadata"]
            
            # Check scheme prefix
            self.assertTrue(text.startswith("Scheme: HDFC Mid-Cap Opportunities Fund (also known as HDFC Mid-Cap Fund) (Direct)\nContent: "))
            # Check length ceiling
            self.assertTrue(len(text) <= 384, f"Enriched chunk exceeded 384 limit: {len(text)}")
            # Check metadata schema matching
            self.assertEqual(meta["source_file"], filename)
            self.assertEqual(meta["scheme_name"], "HDFC Mid-Cap Opportunities Fund (also known as HDFC Mid-Cap Fund) (Direct)")
            self.assertEqual(meta["source_url"], "https://www.hdfcfund.com/explore/mutual-funds/hdfc-mid-cap-fund/direct")

    def test_embedding_service_dimensions(self):
        """Verify that BGE Small generates 384-dimensional normalized embeddings."""
        embed_service = EmbeddingService(model_name="BAAI/bge-small-en-v1.5")
        
        # Test document embedding (no prefix)
        docs = ["Hello mutual fund investor", "What is the exit load?"]
        embeddings = embed_service.embed_documents(docs)
        
        self.assertEqual(embeddings.shape, (2, 384))
        self.assertEqual(embeddings.dtype, np.float32)
        
        # Test cosine normalization (magnitude should be 1.0)
        for emb in embeddings:
            magnitude = np.linalg.norm(emb)
            self.assertAlmostEqual(magnitude, 1.0, places=5)
            
        # Test query embedding (includes prefix internally)
        query_emb = embed_service.embed_query("Is there an exit load?")
        self.assertEqual(query_emb.shape, (384,))
        self.assertAlmostEqual(np.linalg.norm(query_emb), 1.0, places=5)

    def test_indexer_build_and_atomic_swaps(self):
        """Verify that indexer builds Chroma DB index and directory swaps occur atomically."""
        # Setup temporary mock directory to test indexing in isolation
        mock_clean_dir = os.path.join(self.test_data_dir, "test_mock_cleaned")
        os.makedirs(mock_clean_dir, exist_ok=True)
        
        mock_file = os.path.join(mock_clean_dir, "explore_mutual-funds_hdfc-small-cap-fund_direct.txt")
        with open(mock_file, "w", encoding="utf-8") as f:
            f.write(self.test_text)
            
        # Resolved output chroma db paths
        chroma_dir = self.test_chroma_dir
        old_chroma_dir = chroma_dir + "_old"
        temp_chroma_dir = chroma_dir + "_temp"
        
        try:
            # Build index
            success = build_index(
                cleaned_dir=mock_clean_dir,
                index_path=self.test_index_path,
                meta_path=self.test_meta_path,
                model_name="BAAI/bge-small-en-v1.5"
            )
            
            self.assertTrue(success)
            self.assertTrue(os.path.exists(chroma_dir))
            self.assertFalse(os.path.exists(temp_chroma_dir))
            
            # Verify Chroma DB contains the added documents
            client = chromadb.PersistentClient(path=chroma_dir)
            collection = client.get_collection(name="hdfc_mutual_funds")
            
            results = collection.get()
            self.assertTrue(len(results["ids"]) > 0)
            
            # Check metadata schema matching
            first_meta = results["metadatas"][0]
            self.assertEqual(first_meta["scheme_name"], "HDFC Small-Cap Fund (Direct)")
            self.assertEqual(first_meta["source_file"], "explore_mutual-funds_hdfc-small-cap-fund_direct.txt")
            
            if hasattr(client, "close"):
                client.close()
            else:
                del collection
                del client
                gc.collect()
            
        finally:
            # Cleanup test directories/files
            if os.path.exists(mock_file):
                os.remove(mock_file)
            if os.path.exists(mock_clean_dir):
                os.rmdir(mock_clean_dir)
            if os.path.exists(self.test_index_path):
                os.remove(self.test_index_path)
            if os.path.exists(self.test_meta_path):
                os.remove(self.test_meta_path)
            
            # Wait a split second and clean up chroma folders created during tests
            time.sleep(0.5)
            for path in [old_chroma_dir, temp_chroma_dir]:
                if os.path.exists(path):
                    try: delete_directory_with_retry(path)
                    except: pass

    def test_semantic_retriever_query(self):
        """Verify retriever query retrieval succeeds and resolves scheme URLs with high confidence (>0.7)."""
        # Run search query on the production database
        if not os.path.exists(os.path.join(self.test_data_dir, "chroma_db")):
            logger.warning("Production Chroma DB not found, skipping retrieval tests. Build index first.")
            return
            
        retriever = SemanticRetriever(index_dir=self.test_data_dir)
        results = retriever.retrieve("HDFC Small Cap exit load", top_k=2)
        
        self.assertTrue(len(results) > 0, "Retriever returned 0 results.")
        
        # Verify first result is indeed HDFC Small Cap Fund and has high confidence
        top_match = results[0]
        logger.info(f"Top Match Confidence: {top_match['confidence']:.4f} for URL: {top_match['metadata']['source_url']}")
        
        self.assertEqual(top_match["metadata"]["scheme_name"], "HDFC Small-Cap Fund (Direct)")
        self.assertEqual(top_match["metadata"]["source_url"], "https://www.hdfcfund.com/explore/mutual-funds/hdfc-small-cap-fund/direct")
        
        # Phase 2 Verification Plan metric: Confidence score above 0.7
        self.assertTrue(top_match["confidence"] > 0.7, 
                        f"Confidence score {top_match['confidence']} was below threshold 0.7")

if __name__ == "__main__":
    import time
    unittest.main()
