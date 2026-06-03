import os
import logging
from typing import List, Dict

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Grounded mapping of filenames to official Scheme / Page Titles as defined in docs/corpus.md
FILENAME_TO_SCHEME = {
    "nav-and-idcw.txt": "NAV & IDCW Tracking",
    "mutual-funds_factsheets.txt": "Scheme Factsheets",
    "downloads_monthly-fortnightly-scheme-portfolio.txt": "Monthly & Fortnightly Scheme Portfolios",
    "investors_total-expense-ratio.txt": "Total Expense Ratio (TER)",
    "learn_blog.txt": "Learn / Mutual Funds Blog Portal",
    "learn_blog_what-nav-mutual-funds.txt": "Understanding Net Asset Value (NAV)",
    "learn_blog_what-are-open-ended-and-close-ended-mutual-fund-schemes.txt": "Open-Ended vs. Close-Ended Schemes",
    "learn_blog_understanding-debt-mutual-fund-schemes-meaning-and-how-they-work.txt": "Understanding Debt Mutual Fund Schemes",
    "about-us.txt": "About Us",
    "downloads_forms.txt": "Downloads Portal / Request Forms",
    "contact-us_investor-relationship-officer.txt": "Contact Us / Investor Relationship Officer",
    "explore_mutual-funds_hdfc-mid-cap-fund_direct.txt": "HDFC Mid-Cap Opportunities Fund (also known as HDFC Mid-Cap Fund) (Direct)",
    "explore_mutual-funds_hdfc-large-cap-fund_direct.txt": "HDFC Top 100 Fund (also known as HDFC Large-Cap Fund) (Direct)",
    "explore_mutual-funds_hdfc-large-and-mid-cap-fund_direct.txt": "HDFC Large & Mid-Cap Fund (Direct)",
    "explore_mutual-funds_hdfc-small-cap-fund_direct.txt": "HDFC Small-Cap Fund (Direct)",
    "explore_mutual-funds_hdfc-gold-etf-fund-fund_direct.txt": "HDFC Gold ETF Fund (also known as HDFC Gold Fund) (Direct)",
    "explore_mutual-funds_hdfc-silver-etf-fund-fund_direct.txt": "HDFC Silver ETF Fund (Direct)"
}

# Mapping of filenames back to their HDFC source URLs
FILENAME_TO_URL = {
    "nav-and-idcw.txt": "https://www.hdfcfund.com/nav-and-idcw",
    "mutual-funds_factsheets.txt": "https://www.hdfcfund.com/mutual-funds/factsheets",
    "downloads_monthly-fortnightly-scheme-portfolio.txt": "https://www.hdfcfund.com/downloads/monthly-fortnightly-scheme-portfolio",
    "investors_total-expense-ratio.txt": "https://www.hdfcfund.com/investors/total-expense-ratio",
    "learn_blog.txt": "https://www.hdfcfund.com/learn/blog",
    "learn_blog_what-nav-mutual-funds.txt": "https://www.hdfcfund.com/learn/blog/what-nav-mutual-funds",
    "learn_blog_what-are-open-ended-and-close-ended-mutual-fund-schemes.txt": "https://www.hdfcfund.com/learn/blog/what-are-open-ended-and-close-ended-mutual-fund-schemes",
    "learn_blog_understanding-debt-mutual-fund-schemes-meaning-and-how-they-work.txt": "https://www.hdfcfund.com/learn/blog/understanding-debt-mutual-fund-schemes-meaning-and-how-they-work",
    "about-us.txt": "https://www.hdfcfund.com/about-us",
    "downloads_forms.txt": "https://www.hdfcfund.com/downloads/forms",
    "contact-us_investor-relationship-officer.txt": "https://www.hdfcfund.com/contact-us/investor-relationship-officer",
    "explore_mutual-funds_hdfc-mid-cap-fund_direct.txt": "https://www.hdfcfund.com/explore/mutual-funds/hdfc-mid-cap-fund/direct",
    "explore_mutual-funds_hdfc-large-cap-fund_direct.txt": "https://www.hdfcfund.com/explore/mutual-funds/hdfc-large-cap-fund/direct",
    "explore_mutual-funds_hdfc-large-and-mid-cap-fund_direct.txt": "https://www.hdfcfund.com/explore/mutual-funds/hdfc-large-and-mid-cap-fund/direct",
    "explore_mutual-funds_hdfc-small-cap-fund_direct.txt": "https://www.hdfcfund.com/explore/mutual-funds/hdfc-small-cap-fund/direct",
    "explore_mutual-funds_hdfc-gold-etf-fund-fund_direct.txt": "https://www.hdfcfund.com/explore/mutual-funds/hdfc-gold-etf-fund-fund/direct",
    "explore_mutual-funds_hdfc-silver-etf-fund-fund_direct.txt": "https://www.hdfcfund.com/explore/mutual-funds/hdfc-silver-etf-fund-fund/direct"
}

def get_scheme_name(filename: str) -> str:
    """Resolve filename to official scheme/page title."""
    base = os.path.basename(filename)
    if base in FILENAME_TO_SCHEME:
        return FILENAME_TO_SCHEME[base]
    # General formatting fallback
    name = base.replace(".txt", "").replace(".html", "")
    name = name.replace("explore_mutual-funds_", "").replace("_direct", "")
    return name.replace("_", " ").replace("-", " ").title()

def get_scheme_url(filename: str) -> str:
    """Resolve filename to official HDFC source URL."""
    base = os.path.basename(filename)
    if base in FILENAME_TO_URL:
        return FILENAME_TO_URL[base]
    # Fallback to base domain
    return "https://www.hdfcfund.com"

class SimpleRecursiveSplitter:
    """Lightweight custom Recursive Character Text Splitter."""
    def __init__(self, chunk_size: int = 384, chunk_overlap: int = 80, separators: List[str] = None):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.separators = separators or ["\n\n", "\n", ". ", " ", ""]

    def _recursive_split(self, text: str, separators: List[str], chunk_size: int, chunk_overlap: int) -> List[str]:
        text = text.strip()
        if not text:
            return []
        if len(text) <= chunk_size:
            return [text]

        # Find the highest-priority separator present in text
        selected_sep = None
        selected_index = -1
        for i, sep in enumerate(separators):
            if sep in text:
                selected_sep = sep
                selected_index = i
                break

        if selected_sep is None:
            # Fallback to character chunking if no separator is found
            chunks = []
            start = 0
            while start < len(text):
                end = start + chunk_size
                chunks.append(text[start:end])
                start += chunk_size - chunk_overlap
            return chunks

        # Split text by selected separator
        parts = text.split(selected_sep)
        chunks = []
        current_chunk = []
        current_length = 0

        for part in parts:
            part_len = len(part)
            # If a single part exceeds target chunk size, split it recursively using remaining separators
            if part_len > chunk_size:
                # Emit accumulated elements first
                if current_chunk:
                    chunks.append(selected_sep.join(current_chunk))
                    current_chunk = []
                    current_length = 0
                
                sub_chunks = self._recursive_split(part, separators[selected_index + 1:], chunk_size, chunk_overlap)
                chunks.extend(sub_chunks)
            else:
                sep_len = len(selected_sep) if current_chunk else 0
                if current_length + sep_len + part_len <= chunk_size:
                    current_chunk.append(part)
                    current_length += sep_len + part_len
                else:
                    # Emit current accumulated chunk
                    if current_chunk:
                        chunks.append(selected_sep.join(current_chunk))
                    
                    # Compute overlap using backward accumulation from previous chunk elements
                    overlap_chunk = []
                    overlap_len = 0
                    if current_chunk:
                        for p in reversed(current_chunk):
                            p_sep_len = len(selected_sep) if overlap_chunk else 0
                            new_overlap_len = overlap_len + p_sep_len + len(p)
                            # Ensure overlap length respects targets AND does not force the new chunk to exceed chunk_size
                            new_total_len = new_overlap_len + (len(selected_sep) if new_overlap_len else 0) + part_len
                            if new_overlap_len <= chunk_overlap and new_total_len <= chunk_size:
                                overlap_chunk.insert(0, p)
                                overlap_len = new_overlap_len
                            else:
                                break
                    
                    # Start new chunk with overlap elements + current part
                    current_chunk = overlap_chunk + [part]
                    current_length = overlap_len + (len(selected_sep) if overlap_chunk else 0) + part_len

        if current_chunk:
            chunks.append(selected_sep.join(current_chunk))

        return chunks

    def split_text(self, text: str) -> List[str]:
        return self._recursive_split(text, self.separators, self.chunk_size, self.chunk_overlap)


def chunk_document(filename: str, clean_text: str, chunk_size: int = 384, chunk_overlap: int = 80) -> List[Dict]:
    """Split clean document text and prepend contextual scheme info."""
    scheme_name = get_scheme_name(filename)
    source_url = get_scheme_url(filename)
    
    # Prefix format: "Scheme: <Scheme Name>\nContent: "
    prefix = f"Scheme: {scheme_name}\nContent: "
    prefix_len = len(prefix)
    
    # Adjust base chunk size to ensure prefix + base_chunk <= chunk_size
    adjusted_chunk_size = max(chunk_size - prefix_len, 100)
    adjusted_overlap = min(chunk_overlap, int(adjusted_chunk_size * 0.25))
    
    splitter = SimpleRecursiveSplitter(
        chunk_size=adjusted_chunk_size, 
        chunk_overlap=adjusted_overlap
    )
    base_chunks = splitter.split_text(clean_text)
    
    enriched_chunks = []
    for idx, base in enumerate(base_chunks):
        enriched_text = f"{prefix}{base}"
        enriched_chunks.append({
            "text": enriched_text,
            "metadata": {
                "source_file": os.path.basename(filename),
                "scheme_name": scheme_name,
                "source_url": source_url,
                "chunk_index": idx
            }
        })
        
    return enriched_chunks
