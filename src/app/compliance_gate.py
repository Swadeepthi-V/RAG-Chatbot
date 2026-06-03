import re
import logging
import numpy as np
from typing import Dict, Tuple, Optional
from embeddings import EmbeddingService

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# SEBI/AMFI Compliant Refusal Templates
PII_REFUSAL_MESSAGE = "For your security, please do not share account numbers, PAN details, or other personal identifiers. Query rejected."

ADVISORY_REFUSAL_MESSAGE = (
    "I am a facts-only assistant for HDFC Mutual Fund schemes. I cannot provide investment advice, "
    "returns predictions, or subjective recommendations. Please consult a SEBI-registered financial "
    "advisor or review investor education resources on AMFI: https://www.amfiindia.com"
)

PERFORMANCE_BYPASS_MESSAGE = (
    "I cannot compare schemes, calculate future returns, or state which fund is better. "
    "You can review the official performance summaries on the HDFC Factsheets here: "
    "https://www.hdfcfund.com/mutual-funds/factsheets"
)

# Textual digits conversion map for obfuscated PII detection
WORD_TO_NUM = {
    "zero": "0", "one": "1", "two": "2", "three": "3", "four": "4",
    "five": "5", "six": "6", "seven": "7", "eight": "8", "nine": "9"
}

# Fast check keywords list indicating Advisory / Comparison
ADVISORY_KEYWORDS = [
    r"\bshould\s+i\s+(?:buy|sell|invest|choose)\b",
    r"\bwhich\s+(?:fund|scheme|etf)\s+is\s+(?:better|best|worst|good)\b",
    r"\bwould\s+you\s+(?:recommend|advise)\b",
    r"\bis\s+it\s+good\s+to\s+invest\b",
    r"\bgive\s+me\s+investment\s+advice\b",
    r"\bpredict\s+(?:future|growth|returns)\b",
    r"\bhow\s+much\s+profit\s+will\b",
    r"\bwhich\s+one\s+should\s+i\b",
    r"\bcompare\s+hdfc\b",
    r"\bhigher\s+returns\s+than\b",
    r"\bbetter\s+investment\b"
]

# Keywords indicating Performance factsheet bypass
PERFORMANCE_KEYWORDS = [
    r"\bperformance\b",
    r"\breturns\b",
    r"\byield\b",
    r"\bprofit\b",
    r"\bhistorical\b",
    r"\bvs\b",
    r"\bversus\b",
    r"\boutperform\b"
]

# Query Classifier Prototypes for Semantic Zero-Shot Routing
ADVISORY_PROTOTYPES = [
    "Should I invest in HDFC Mid-Cap Fund?",
    "Which mutual fund is better for retirement?",
    "Is HDFC Small Cap Fund a buy or sell?",
    "Will I make a profit in HDFC Large Cap?",
    "Give me investment advice for mutual funds.",
    "Recommend a fund to invest in.",
    "Is HDFC Mid-Cap better than HDFC Small Cap?",
    "Which is the best fund to buy today?"
]

FACTUAL_PROTOTYPES = [
    "What is the exit load of HDFC Mid-Cap Fund?",
    "What is the expense ratio of HDFC Small Cap?",
    "Who is the fund manager of HDFC Large Cap?",
    "What is the minimum SIP amount for HDFC Gold ETF?",
    "How do I download the capital gains statement?",
    "What is the riskometer rating of HDFC Silver ETF?",
    "What is the lock-in period of ELSS?",
    "What is the NAV of HDFC Mid-Cap Fund?",
    "What is the Net Asset Value of HDFC Top 100 Fund?",
    "Show current NAV for HDFC Small Cap Fund."
]


class IngressComplianceGate:
    """Sanitizes queries for PII leakages and classifies intent to enforce compliance guardrails."""
    def __init__(self, embed_service: Optional[EmbeddingService] = None):
        self.embed_service = embed_service
        self.advisory_proto_embs = None
        self.factual_proto_embs = None
        
    def check_pii(self, query: str) -> Optional[str]:
        """Scan queries for PAN, Aadhaar, Credit Card, Email, and Phone PII details, including obfuscated spacing/words."""
        # 1. Basic normalization (strip common dividers)
        normalized = query.replace(" ", "").replace("-", "").replace(".", "").replace(",", "")
        
        # 2. Textual digit translation (obfuscated numeric words check)
        normalized_lower = normalized.lower()
        for word, num in WORD_TO_NUM.items():
            normalized_lower = normalized_lower.replace(word, num)
            
        # 3. PAN check (5 letters, 4 digits, 1 letter)
        pan_pattern = re.compile(r'[a-zA-Z]{5}\d{4}[a-zA-Z]')
        if pan_pattern.search(query) or pan_pattern.search(normalized) or pan_pattern.search(normalized_lower):
            return PII_REFUSAL_MESSAGE
            
        # 4. Aadhaar check (12 digits)
        aadhaar_pattern = re.compile(r'\b\d{12}\b')
        if aadhaar_pattern.search(normalized_lower) or re.search(r'\b\d{4}[ -]?\d{4}[ -]?\d{4}\b', query):
            return PII_REFUSAL_MESSAGE
            
        # 5. Credit Card check (16 digits)
        card_pattern = re.compile(r'\b\d{16}\b')
        if card_pattern.search(normalized_lower) or re.search(r'\b(?:\d{4}[ -]?){3}\d{4}\b', query):
            return PII_REFUSAL_MESSAGE
            
        # 6. Email check
        email_pattern = re.compile(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}')
        if email_pattern.search(query):
            return PII_REFUSAL_MESSAGE
            
        # 7. Indian Mobile/Phone check (10 digits starting with optional +91 or 0)
        phone_pattern = re.compile(r'\b(?:\+91|0)?[6-9]\d{9}\b')
        if phone_pattern.search(query) or re.search(r'\b[6-9]\d{9}\b', normalized_lower):
            return PII_REFUSAL_MESSAGE
            
        return None

    def _lazy_load_prototypes(self):
        """Pre-embed prototypical classification query sets lazily on first semantic request."""
        if self.advisory_proto_embs is None or self.factual_proto_embs is None:
            if self.embed_service is None:
                self.embed_service = EmbeddingService()
                
            logger.info("IngressComplianceGate: Pre-embedding semantic classification prototypes...")
            self.advisory_proto_embs = self.embed_service.embed_documents(ADVISORY_PROTOTYPES)
            self.factual_proto_embs = self.embed_service.embed_documents(FACTUAL_PROTOTYPES)
            logger.info("IngressComplianceGate: Pre-embedding complete.")

    def classify_query(self, query: str) -> Tuple[str, float]:
        """Classify query intent into: 'factual', 'advisory', or 'performance'."""
        query_lower = query.lower()
        
        # 1. Fast Keyword Interceptors (Under 1ms bypass)
        for pattern in ADVISORY_KEYWORDS:
            if re.search(pattern, query_lower):
                logger.info(f"Compliance Gate: Short-circuit keyword match classified query as 'advisory'")
                return "advisory", 1.0
                
        for pattern in PERFORMANCE_KEYWORDS:
            if re.search(pattern, query_lower):
                logger.info(f"Compliance Gate: Short-circuit keyword match classified query as 'performance'")
                return "performance", 1.0
                
        # 2. Semantic Zero-Shot Classifier
        try:
            self._lazy_load_prototypes()
            query_vector = self.embed_service.embed_query(query)
            
            # Compute cosine similarities (dot products since vectors are normalized L2)
            advisory_sims = np.dot(self.advisory_proto_embs, query_vector)
            factual_sims = np.dot(self.factual_proto_embs, query_vector)
            
            max_advisory = float(np.max(advisory_sims))
            max_factual = float(np.max(factual_sims))
            
            logger.info(f"Semantic match scores - Advisory: {max_advisory:.4f}, Factual: {max_factual:.4f}")
            
            # Classification threshold rule
            if max_advisory > max_factual and max_advisory > 0.65:
                return "advisory", max_advisory
            elif max_factual > max_advisory and max_factual > 0.65:
                return "factual", max_factual
            else:
                # Default safety behavior: if ambiguous, classify as factual to allow retriever database lookup
                return "factual", max(max_factual, max_advisory)
                
        except Exception as e:
            logger.error(f"Error during semantic query classification: {e}")
            # Safe baseline fallback
            return "factual", 0.5

    def route_query(self, query: str) -> Optional[Dict[str, str]]:
        """Evaluate the query compliance status. Returns refusal dictionary if blocked, or None if safe."""
        # 1. PII Scan
        pii_warning = self.check_pii(query)
        if pii_warning:
            logger.info("Compliance Gate: Privacy gate triggered on query.")
            return {"status": "blocked", "category": "pii", "response": pii_warning}
            
        # 2. Intent Classification
        category, confidence = self.classify_query(query)
        
        if category == "advisory":
            logger.info(f"Compliance Gate: Intercepted advisory intent (Confidence: {confidence:.4f})")
            return {"status": "blocked", "category": "advisory", "response": ADVISORY_REFUSAL_MESSAGE}
            
        elif category == "performance":
            logger.info(f"Compliance Gate: Intercepted performance/comparison bypass query")
            return {"status": "blocked", "category": "performance", "response": PERFORMANCE_BYPASS_MESSAGE}
            
        logger.info("Compliance Gate: Query passed compliance gate.")
        return None
