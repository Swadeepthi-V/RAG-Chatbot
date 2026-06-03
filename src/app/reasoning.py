"""Reasoning and Egress Gate Module (Phase 4)."""

import os
import re
import logging
import requests
from typing import List, Dict, Optional

logger = logging.getLogger("uvicorn")

def split_sentences(text: str) -> List[str]:
    """Split text into sentences, preserving periods inside abbreviations, URLs, and decimal numbers."""
    text = text.strip()
    if not text:
        return []
        
    sentences = []
    current = []
    words = text.split()
    
    # Common abbreviations in financial/mutual fund documents that shouldn't end a sentence
    abbreviations = {
        "ltd.", "co.", "corp.", "p.a.", "e.g.", "i.e.", "vs.", "amc.", "aum.", 
        "no.", "inc.", "mr.", "mrs.", "ms.", "dr.", "rs.", "cr.", "sh.", "org."
    }
    
    for word in words:
        current.append(word)
        # Check if the word ends with terminal punctuation: . or ? or !
        if word and word[-1] in {'.', '?', '!'}:
            word_lower = word.lower()
            
            # Strip trailing punctuation for abbreviation/number checks
            clean_word = word_lower.rstrip('.!?')
            
            is_abbr = word_lower in abbreviations or (clean_word + ".") in abbreviations
            is_initial = len(clean_word) == 1 and clean_word.isalpha()
            is_number = clean_word.replace(",", "").replace(".", "").isdigit()
            
            # Don't split if it's an abbreviation, single letter initial, or number
            if not is_abbr and not is_initial and not is_number:
                sentences.append(" ".join(current))
                current = []
                
    if current:
        sentences.append(" ".join(current))
        
    return sentences


class LLMReasoningEngine:
    """Manages constrained generation calls to Groq and validates the egress response quality."""
    
    def __init__(self):
        self.api_url = "https://api.groq.com/openai/v1/chat/completions"
        self.api_key = os.getenv("GROQ_API_KEY", "").strip()
        self.model = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant").strip()
        self.timeout = 5.0  # Strict 5-second timeout
        
    def _fallback_response(self, query: str, top_chunk: Dict) -> str:
        """Fallback response when Groq is unavailable or key is missing.
        Uses the top retrieved semantic chunk directly, applying length and citation constraints.
        """
        logger.warning("LLMReasoningEngine: Using fallback response generation.")
        text = top_chunk.get("text", "")
        source_url = top_chunk.get("metadata", {}).get("source_url", "")
        
        # Split and take up to 3 sentences
        sentences = split_sentences(text)
        truncated_text = " ".join(sentences[:3])
        
        # Format the citation at the end
        if source_url:
            truncated_text = f"{truncated_text} [Source]({source_url})"
            
        return truncated_text

    def validate_and_fix_citation(self, text: str, expected_url: str) -> str:
        """Ensures that the text contains EXACTLY one markdown citation link matching the expected URL."""
        # Find all markdown links [text](url)
        markdown_link_pattern = r'\[([^\]]+)\]\((https?://[^\)]+)\)'
        links = re.findall(markdown_link_pattern, text)
        
        # If there is exactly one link and its URL matches the expected source URL, we accept it
        if len(links) == 1 and links[0][1] == expected_url:
            return text
            
        # Otherwise, strip all existing markdown links and plain-text URL mentions of the expected_url,
        # then append a clean citation at the end.
        
        # Replace markdown links with their display text (e.g. [HDFC Fund](url) -> HDFC Fund)
        clean_text = re.sub(markdown_link_pattern, r'\1', text)
        
        # Strip plain occurrences of the expected URL (to avoid double print)
        clean_text = clean_text.replace(expected_url, "")
        
        # Strip extra trailing whitespace or dangling punctuations before adding source
        clean_text = clean_text.strip()
        if clean_text and clean_text[-1] not in {'.', '?', '!'}:
            # Keep clean punctuation ending
            pass
            
        # Append the standardized citation
        return f"{clean_text} [Source]({expected_url})"

    def generate_answer(self, query: str, search_results: List[Dict]) -> str:
        """Sends query and context to Groq Cloud LLM and processes output under strict constraints."""
        if not search_results:
            return "No matching HDFC mutual fund records found in the database index."
            
        top_match = search_results[0]
        source_url = top_match.get("metadata", {}).get("source_url", "")
        
        # If API key is missing, trigger fallback immediately
        if not self.api_key:
            logger.warning("LLMReasoningEngine: GROQ_API_KEY is missing. Falling back to retrieved chunk text.")
            response_text = self._fallback_response(query, top_match)
            return self._append_footer(response_text)
            
        # Format context for system prompt
        context_str = ""
        for i, match in enumerate(search_results[:4]):  # Use top 4 chunks for context
            url = match.get("metadata", {}).get("source_url", "N/A")
            text = match.get("text", "")
            context_str += f"Context Chunk {i+1} (Source URL: {url}):\n{text}\n---\n"
            
        system_prompt = (
            "You are a factual Mutual Fund FAQ Assistant for HDFC Mutual Fund.\n"
            "Answer the query strictly using the provided context chunks.\n"
            "You may resolve common HDFC scheme name variations or abbreviations (e.g. 'HDFC Mid-Cap Fund' refers to 'HDFC Mid-Cap Opportunities Fund', and 'HDFC Large-Cap Fund' refers to 'HDFC Top 100 Fund').\n"
            "If the user asks to share, show, or download a factsheet, document, or form, and the filename of that document is listed in the context (e.g., under 'Downloads'), state the filename and mention that it is available for download at the cited source URL.\n"
            "Do not assume, guess, or extrapolate facts not present in the context.\n"
            "If the context does not contain the answer, reply exactly with: "
            "\"I'm sorry, but I cannot find that information in the HDFC Mutual Fund documents.\"\n"
            "Do not provide investment advice, recommendations, predictions, or subjective opinions.\n"
            "You MUST include exactly one citation link from the context, formatted exactly as a markdown link, "
            "e.g. [Source](url), where the URL matches the source URL in the context.\n"
            "Keep the response short, concise, and under 3 sentences."
        )
        
        user_prompt = f"Context:\n{context_str}\nQuery: {query}"
        
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": 0.0,
            "max_tokens": 300
        }
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        try:
            logger.info(f"LLMReasoningEngine: Sending API request to Groq using model: {self.model}")
            res = requests.post(self.api_url, json=payload, headers=headers, timeout=self.timeout)
            
            if res.status_code == 200:
                result_json = res.json()
                raw_answer = result_json["choices"][0]["message"]["content"].strip()
                logger.info("LLMReasoningEngine: Received response successfully.")
                
                # Apply Egress Gate 1: Length Guard (Truncate beyond 3 sentences)
                sentences = split_sentences(raw_answer)
                truncated_answer = " ".join(sentences[:3])
                
                # Apply Egress Gate 2: Citation Validator (Ensure exactly one valid markdown link)
                final_answer = self.validate_and_fix_citation(truncated_answer, source_url)
                
                return self._append_footer(final_answer)
            else:
                logger.error(f"LLMReasoningEngine: Groq API returned status code {res.status_code}: {res.text}")
                fallback = self._fallback_response(query, top_match)
                return self._append_footer(fallback)
                
        except requests.exceptions.RequestException as e:
            logger.error(f"LLMReasoningEngine: Groq API connection failed: {e}")
            fallback = self._fallback_response(query, top_match)
            return self._append_footer(fallback)

    def _append_footer(self, text: str) -> str:
        """Appends the index update timestamp footer to the response."""
        update_date = os.getenv("INDEX_UPDATE_DATE", "02-Jun-2026")
        footer = f"\n\nLast updated from sources: {update_date}"
        return f"{text}{footer}"
