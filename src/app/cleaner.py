import os
import re
import html
import logging
from bs4 import BeautifulSoup

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# HTML tags to remove entirely (including their contents)
UNWANTED_TAGS = [
    "script", "style", "noscript", "iframe", "svg", "form", "aside", 
    "header", "footer", "nav", "button", "select", "option", "input"
]

# Keywords in classes or IDs that indicate boilerplate / layout grids (header, footer, cookie popups, modals)
UNWANTED_KEYWORDS = [
    "cookie", "popup", "pop-up", "modal", "dialog", "banner", 
    "promo", "sidebar", "social-share", "share-links", "nav-links", 
    "navbar", "menu", "chat-widget"
]

def clean_html_content(html_content: str) -> str:
    """Parse raw HTML, strip boilerplate, decode entities, and normalize whitespace."""
    if not html_content:
        return ""
    
    # 1. Parse with BeautifulSoup
    soup = BeautifulSoup(html_content, "html.parser")
    
    # 2. Decompose unwanted tags
    for tag in UNWANTED_TAGS:
        for element in soup.find_all(tag):
            element.decompose()
            
    # 3. Decompose elements matching boilerplate class/ID keywords
    for element in soup.find_all(True):
        # Skip elements that have already been decomposed (their parent or attrs is None)
        if element.parent is None or element.attrs is None:
            continue
            
        # Examine attributes
        classes = element.get("class", [])
        if isinstance(classes, list):
            classes_str = " ".join(classes).lower()
        else:
            classes_str = str(classes).lower()
            
        el_id = str(element.get("id", "")).lower()
        role = str(element.get("role", "")).lower()
        aria_hidden = str(element.get("aria-hidden", "")).lower()
        
        # Determine if we should decompose
        should_remove = False
        
        # Broad checks for dialogs or hidden elements
        if role in ["dialog", "alertdialog"] or aria_hidden == "true":
            should_remove = True
            
        # Target specific boilerplate keywords (avoiding broad collisions like 'header' matching 'section-header')
        for kw in UNWANTED_KEYWORDS:
            if kw in classes_str or kw in el_id:
                # Extra safety: check we don't accidentally drop core content containers
                if "content" in classes_str or "main" in classes_str or "detail" in classes_str:
                    continue
                should_remove = True
                break
                
        # Specific match for header/footer classes (exactly matching or starting with)
        for hf in ["header", "footer"]:
            if classes_str == hf or classes_str.startswith(f"{hf}-") or el_id == hf or el_id.startswith(f"{hf}-"):
                # Safety: check we don't match section headers or page titles
                if not ("title" in classes_str or "section" in classes_str or "card" in classes_str):
                    should_remove = True
                    
        if should_remove:
            element.decompose()
            
    # 4. Extract text
    raw_text = soup.get_text(separator="\n")
    
    # 5. Decode HTML/Unicode entities
    # html.unescape handles entities like &nbsp;, &amp;, &#8377;, etc.
    decoded_text = html.unescape(raw_text)
    
    # Standardize common Unicode characters (like replacement of non-breaking spaces \xa0, \u20b9 for Rupee, etc.)
    decoded_text = decoded_text.replace("\xa0", " ")
    decoded_text = decoded_text.replace("\u200b", "")  # zero-width space
    # Standardize Rupee symbol variants
    decoded_text = decoded_text.replace("Rs.", "₹").replace("Rs ", "₹ ")
    
    # 6. Normalize whitespace
    lines = decoded_text.splitlines()
    cleaned_lines = []
    
    for line in lines:
        # Collapse multiple internal spaces/tabs to a single space
        line = re.sub(r"[ \t]+", " ", line).strip()
        if line:
            cleaned_lines.append(line)
            
    # Reassemble and collapse multiple empty lines down to at most double newlines
    # Since we stripped empty lines from our list, joining them with \n represents single-spaced lines.
    # To preserve some paragraphs or logical breaks, we can insert newlines based on structural headers or tables.
    # A standard way is to join with \n. Let's do that and then run a simple whitespace compression:
    text_content = "\n".join(cleaned_lines)
    
    return text_content

def clean_file(raw_filepath: str, output_filepath: str) -> bool:
    """Clean a single raw HTML file and save the results as text."""
    try:
        if not os.path.exists(raw_filepath):
            logger.error(f"Raw HTML file not found: {raw_filepath}")
            return False
            
        with open(raw_filepath, "r", encoding="utf-8") as f:
            html_content = f.read()
            
        cleaned_text = clean_html_content(html_content)
        
        # Ensure output directory exists
        os.makedirs(os.path.dirname(output_filepath), exist_ok=True)
        
        with open(output_filepath, "w", encoding="utf-8") as f:
            f.write(cleaned_text)
            
        logger.info(f"Successfully cleaned and saved to {output_filepath}")
        return True
        
    except Exception as e:
        logger.error(f"Error cleaning file {raw_filepath}: {e}")
        return False

def clean_all(raw_dir: str, output_dir: str) -> int:
    """Clean all HTML files found in the raw_dir, saving to output_dir."""
    if not os.path.exists(raw_dir):
        logger.warning(f"Raw HTML directory does not exist: {raw_dir}")
        return 0
        
    count = 0
    for filename in os.listdir(raw_dir):
        if filename.endswith(".html"):
            raw_filepath = os.path.join(raw_dir, filename)
            txt_filename = filename.replace(".html", ".txt")
            output_filepath = os.path.join(output_dir, txt_filename)
            
            if clean_file(raw_filepath, output_filepath):
                count += 1
                
    return count

if __name__ == "__main__":
    # Local CLI testing run
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    raw_dir = os.path.join(base_dir, "data", "raw_html")
    output_dir = os.path.join(base_dir, "data", "cleaned_text")
    logger.info(f"Running standalone cleaner. Input: {raw_dir}, Output: {output_dir}")
    clean_all(raw_dir, output_dir)
