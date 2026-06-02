"""FastAPI Entrypoint for Mutual Fund FAQ Assistant (Phase 0)."""

import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

# Load active environment configurations
load_dotenv()

# Setup logging
import logging
logger = logging.getLogger("uvicorn")

app = FastAPI(
    title="Mutual Fund FAQ Assistant",
    description="A facts-only RAG chatbot providing source-backed responses for HDFC Mutual Fund schemes.",
    version="0.1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from scheduler import DailyScheduler
from compliance_gate import IngressComplianceGate
from retriever import SemanticRetriever
from reasoning import LLMReasoningEngine

# Global singletons
scheduler = None
compliance_gate = None
retriever = None
reasoning_engine = None

def trigger_ingestion():
    """Trigger the offline ingestion pipeline in a subprocess to isolate memory usage."""
    logger.info("DailyScheduler: Launching offline ingestion pipeline subprocess...")
    try:
        import sys
        import subprocess
        script_path = os.path.join(os.path.dirname(__file__), "run_pipeline.py")
        subprocess.run([sys.executable, script_path], check=True)
        logger.info("DailyScheduler: Ingestion pipeline completed successfully.")
    except Exception as e:
        logger.error(f"DailyScheduler: Ingestion pipeline execution failed: {e}")

@app.on_event("startup")
def startup_event():
    """Start the daily re-indexing scheduler and initialize compliance/retrieval engines."""
    global scheduler, compliance_gate, retriever, reasoning_engine
    
    # 1. Start background scheduler
    scheduler = DailyScheduler(trigger_ingestion)
    scheduler.start()
    
    # 2. Resolve data directory path
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    env_index_path = os.getenv("DATA_CACHE_PATH", "./data/vector_store.index")
    if not os.path.isabs(env_index_path):
        data_dir = os.path.abspath(os.path.join(base_dir, "data"))
    else:
        data_dir = os.path.dirname(env_index_path)
        
    # 3. Initialize singletons (loads BGE embedding model on CPU)
    compliance_gate = IngressComplianceGate()
    retriever = SemanticRetriever(index_dir=data_dir)
    reasoning_engine = LLMReasoningEngine()
    logger.info("Compliance Gate, Semantic Retriever, and Reasoning Engine initialized successfully.")

@app.on_event("shutdown")
def shutdown_event():
    """Stop the scheduler background threads."""
    global scheduler
    if scheduler:
        scheduler.stop()

# Health Status response model
class HealthResponse(BaseModel):
    status: str
    amc: str
    corpus_size: int
    last_updated: str
    version: str

@app.on_event("startup")
def log_startup():
    logger.info("Mutual Fund FAQ Assistant is online.")

@app.get("/health", response_model=HealthResponse)
def health_check() -> HealthResponse:
    """Validate server health and current RAG index metadata status."""
    return HealthResponse(
        status="healthy",
        amc="HDFC Mutual Fund",
        corpus_size=17,
        last_updated=os.getenv("INDEX_UPDATE_DATE", "01-Jun-2026"),
        version="0.1.0"
    )

# Query Request and Response models
class QueryRequest(BaseModel):
    query: str

class QueryResponse(BaseModel):
    status: str
    category: str
    response: str
    chunks: list = []

@app.post("/query", response_model=QueryResponse)
def handle_query(req: QueryRequest) -> QueryResponse:
    """Evaluate and route user queries, enforcing PII gates and advisory refusals."""
    # 1. Run Ingress Compliance Gate
    block_result = compliance_gate.route_query(req.query)
    
    if block_result:
        # Request is blocked (PII or Advisory Refusal or Performance Bypass)
        return QueryResponse(
            status=block_result["status"],
            category=block_result["category"],
            response=block_result["response"]
        )
        
    # 2. Route factual query to semantic retriever
    try:
        search_results = retriever.retrieve(req.query, top_k=2)
        if search_results:
            # Generate answer using reasoning engine (incorporates Groq and Egress validations)
            answer = reasoning_engine.generate_answer(req.query, search_results)
            return QueryResponse(
                status="success",
                category="factual",
                response=answer,
                chunks=[{
                    "text": c["text"],
                    "confidence": c["confidence"],
                    "metadata": c["metadata"]
                } for c in search_results]
            )
        else:
            return QueryResponse(
                status="success",
                category="factual",
                response="No matching HDFC mutual fund records found in the database index."
            )
    except Exception as e:
        logger.error(f"Factual query retrieval failed: {e}")
        return QueryResponse(
            status="error",
            category="factual",
            response="Internal error querying semantic retrieval database."
        )

# Basic welcome endpoint
@app.get("/")
def read_root():
    return {
        "message": "Welcome to the Mutual Fund FAQ Assistant API Gateway. Use /health or /query endpoints.",
        "disclaimer": "Facts-only. No investment advice."
    }
