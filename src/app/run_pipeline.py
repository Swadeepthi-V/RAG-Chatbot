import os
import datetime
import logging
from crawler import crawl_all
from cleaner import clean_all
from indexer import build_index
from dotenv import load_dotenv

# Load active environment configurations
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

def update_env_timestamp(new_date_str: str, env_path: str):
    """Update the INDEX_UPDATE_DATE parameter inside the .env file."""
    if not os.path.exists(env_path):
        logger.warning(f".env file not found at {env_path}, skipping update.")
        return
        
    try:
        with open(env_path, "r", encoding="utf-8") as f:
            content = f.read()
            
        # Regex to find and replace INDEX_UPDATE_DATE
        pattern = r"^(INDEX_UPDATE_DATE\s*=.*)$"
        replacement = f"INDEX_UPDATE_DATE={new_date_str}"
        
        if re_match := re_search(pattern, content):
            new_content = re_replace(pattern, replacement, content)
        else:
            # If not present, append it
            new_content = content + f"\nINDEX_UPDATE_DATE={new_date_str}\n"
            
        with open(env_path, "w", encoding="utf-8") as f:
            f.write(new_content)
            
        logger.info(f"Updated .env INDEX_UPDATE_DATE to: {new_date_str}")
    except Exception as e:
        logger.error(f"Failed to update .env timestamp: {e}")

# Helper helper to avoid regex module import error in inline imports
def re_search(pattern, string):
    import re
    return re.search(pattern, string, re.MULTILINE)

def re_replace(pattern, replacement, string):
    import re
    return re.sub(pattern, replacement, string, flags=re.MULTILINE)

def main():
    logger.info("=" * 60)
    logger.info("Starting Phase 1 Ingestion Pipeline: Crawl, Clean & Index")
    logger.info("=" * 60)
    
    # Establish paths
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    raw_dir = os.path.join(base_dir, "data", "raw_html")
    cleaned_dir = os.path.join(base_dir, "data", "cleaned_text")
    env_path = os.path.join(base_dir, ".env")
    
    # Read vector index path from environment variable and resolve it
    env_index_path = os.getenv("DATA_CACHE_PATH", "./data/vector_store.index")
    if not os.path.isabs(env_index_path):
        index_path = os.path.abspath(os.path.join(base_dir, env_index_path))
    else:
        index_path = env_index_path
        
    meta_path = index_path.replace(".index", ".meta")
    
    # Create directories if missing
    os.makedirs(raw_dir, exist_ok=True)
    os.makedirs(cleaned_dir, exist_ok=True)
    os.makedirs(os.path.dirname(index_path), exist_ok=True)
    
    # Step 1: Execute Crawler
    logger.info("Step 1/3: Running Crawler for 17 HDFC Mutual Fund URLs...")
    crawl_results = crawl_all(
        output_dir=raw_dir,
        use_cache_if_failed=True,
        generate_mock_if_missing=True
    )
    
    total_crawled = len(crawl_results)
    successful_crawls = sum(1 for url, status in crawl_results.items() if status)
    logger.info(f"Crawler complete. Status: {successful_crawls}/{total_crawled} URLs succeeded.")
    
    # Step 2: Execute Cleaner/Parser
    logger.info("Step 2/3: Running Cleaner/Parser on scraped HTML content...")
    cleaned_count = clean_all(raw_dir=raw_dir, output_dir=cleaned_dir)
    logger.info(f"Cleaner complete. Processed {cleaned_count} files.")
    
    # Step 3: Execute Chunker, Embedding & Vector Store Indexing
    logger.info("Step 3/3: Running Chunker, Embedding Generator & FAISS Indexer...")
    index_success = build_index(
        cleaned_dir=cleaned_dir,
        index_path=index_path,
        meta_path=meta_path,
        model_name="BAAI/bge-small-en-v1.5"
    )
    
    if index_success:
        logger.info("FAISS vector store and metadata indexing completed successfully.")
    else:
        logger.error("FAISS vector store indexing failed.")
        return
        
    # Step 4: Update timestamp in environment configuration
    current_date = datetime.datetime.now().strftime("%d-%b-%Y")
    update_env_timestamp(current_date, env_path)
    
    logger.info("=" * 60)
    logger.info("Ingestion Pipeline Execution Completed Successfully!")
    logger.info(f"Raw Pages Directory: {raw_dir}")
    logger.info(f"Cleaned Pages Directory: {cleaned_dir}")
    logger.info(f"FAISS Vector Index: {index_path}")
    logger.info(f"Index Metadata File: {meta_path}")
    logger.info("=" * 60)

if __name__ == "__main__":
    main()
