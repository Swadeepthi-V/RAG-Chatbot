import os
import gc
import time
import shutil
import logging
import chromadb
from typing import List
from chunker import chunk_document
from embeddings import EmbeddingService

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

def delete_directory_with_retry(path: str, retries: int = 5, delay: float = 0.5):
    """Attempt to delete a directory recursively, retrying on Windows file lock permission errors."""
    if not os.path.exists(path):
        return
    for i in range(retries):
        try:
            shutil.rmtree(path)
            return
        except PermissionError as e:
            if i == retries - 1:
                logger.error(f"Failed to delete directory {path} after {retries} retries: {e}")
                raise
            time.sleep(delay)

def build_index(cleaned_dir: str, index_path: str, meta_path: str, model_name: str = "BAAI/bge-small-en-v1.5") -> bool:
    """Chunk clean documents, generate embeddings, and build the Chroma DB index atomically."""
    if not os.path.exists(cleaned_dir):
        logger.error(f"Cleaned directory does not exist: {cleaned_dir}")
        return False
        
    logger.info("Starting Chroma DB index building process...")
    all_chunks = []
    
    # 1. Chunk all clean files
    for filename in os.listdir(cleaned_dir):
        if filename.endswith(".txt"):
            filepath = os.path.join(cleaned_dir, filename)
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    text = f.read()
                chunks = chunk_document(filename, text)
                all_chunks.extend(chunks)
            except Exception as e:
                logger.error(f"Error processing file {filename} for chunking: {e}")
                
    if not all_chunks:
        logger.warning("No text chunks generated. Index building aborted.")
        return False
        
    logger.info(f"Successfully generated {len(all_chunks)} chunks across cleaned documents.")
    
    # 2. Extract texts and coordinate metadata lists
    texts = [chunk["text"] for chunk in all_chunks]
    metadata_list = [chunk["metadata"] for chunk in all_chunks]
    
    # 3. Load embedding model and encode chunks
    try:
        embed_service = EmbeddingService(model_name=model_name)
        embeddings = embed_service.embed_documents(texts)
    except Exception as e:
        logger.error(f"Failed to generate embeddings: {e}")
        return False
        
    if embeddings.size == 0:
        logger.error("Generated empty embeddings array.")
        return False
        
    logger.info(f"Embeddings generated with shape: {embeddings.shape}")
    
    # 4. Set up Chroma DB directory paths
    # Resolve the destination directory path for Chroma DB
    chroma_dir = os.path.abspath(os.path.join(os.path.dirname(index_path), "chroma_db"))
    temp_chroma_dir = chroma_dir + "_temp"
    old_chroma_dir = chroma_dir + "_old"
    
    # Ensure temporary directory is clean before building
    if os.path.exists(temp_chroma_dir):
        delete_directory_with_retry(temp_chroma_dir)
        
    # 5. Populate Chroma DB temporary collection
    try:
        client = chromadb.PersistentClient(path=temp_chroma_dir)
        # Cosine distance space configured (1 - cosine_similarity)
        collection = client.get_or_create_collection(
            name="hdfc_mutual_funds",
            metadata={"hnsw:space": "cosine"}
        )
        
        # Prepare inputs for Chroma DB
        ids = [f"chunk_{i}" for i in range(len(texts))]
        embeddings_list = [emb.tolist() for emb in embeddings]
        
        # Add to collection
        collection.add(
            ids=ids,
            embeddings=embeddings_list,
            documents=texts,
            metadatas=metadata_list
        )
        
        logger.info(f"Indexed {len(texts)} documents in temporary Chroma DB collection.")
        
        # 6. Explicitly close the client to release SQLite/HNSW file locks
        if hasattr(client, "close"):
            client.close()
            logger.info("Chroma client closed explicitly.")
        else:
            del collection
            del client
            gc.collect()
        time.sleep(0.5)  # Allow Windows OS file handles to close
        
    except Exception as e:
        logger.error(f"Failed to build temporary Chroma DB: {e}")
        if os.path.exists(temp_chroma_dir):
            try: delete_directory_with_retry(temp_chroma_dir)
            except: pass
        return False
        
    # 7. Perform directory-level atomic swap
    try:
        # Move existing active database out of the way
        if os.path.exists(chroma_dir):
            if os.path.exists(old_chroma_dir):
                delete_directory_with_retry(old_chroma_dir)
            os.rename(chroma_dir, old_chroma_dir)
            
        # Swap temporary database to production path
        os.rename(temp_chroma_dir, chroma_dir)
        logger.info(f"Chroma DB production directory swapped atomically to: {chroma_dir}")
        
        # Clean up old database directory
        if os.path.exists(old_chroma_dir):
            delete_directory_with_retry(old_chroma_dir)
            
        return True
    except Exception as e:
        logger.error(f"Atomic folder swap failed: {e}")
        # Rollback: restore old database if swap failed
        if os.path.exists(old_chroma_dir) and not os.path.exists(chroma_dir):
            try: os.rename(old_chroma_dir, chroma_dir)
            except: pass
        return False

if __name__ == "__main__":
    # Local CLI testing run
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    cleaned_dir = os.path.join(base_dir, "data", "cleaned_text")
    index_path = os.path.join(base_dir, "data", "vector_store.index")
    meta_path = os.path.join(base_dir, "data", "vector_store.meta")
    build_index(cleaned_dir, index_path, meta_path)
