# Implementation Plan: Mutual Fund FAQ Assistant

This implementation plan translates the **Mutual Fund FAQ Assistant** (Facts-Only Q&A) architecture into ordered, phase-wise delivery milestones. Each phase delivers a working, testable increment of the system, keeping regulatory compliance, privacy, and speed as core benchmarks.

---

## 📅 Timeline & Phase Overview

The project is structured into **seven sequential phases**:

```mermaid
gantt
    title Implementation Timeline (Phase-Wise)
    dateFormat YYYY-MM-DD
    section Setup
    Phase 0: Setup & Foundation         :active, p0, 2026-06-01, 2d
    section Offline Data
    Phase 1: Daily Ingestion Pipeline   :p1, after p0, 4d
    section Retrieval
    Phase 2: Semantic Retrieval Index  :p2, after p1, 3d
    section Compliance Gate
    Phase 3: Ingress Routing & PII Gate :p3, after p2, 3d
    section LLM & Validator
    Phase 4: LLM reasoning & Egress Gate:p4, after p3, 4d
    section Frontend
    Phase 5: Groww-Inspired UI         :p5, after p4, 4d
    section Hardening
    Phase 6: Testing & Optimization     :p6, after p5, 3d
```

| Phase | Milestone | Primary Outcome | Architecture Alignment |
|---|---|---|---|
| **0** | Project Setup & Foundation | Working repository with environment configs and skeleton | Presentation & Application Gateways |
| **1** | Offline Ingestion Pipeline | Crawler scraping and cleaning the 17 HDFC URLs daily | Offline Ingestion Pipeline |
| **2** | Semantic Retrieval Layer | In-memory index returning matched chunks + URL links | Retrieval Layer |
| **3** | Ingress Query Classifier | Advisory intercepts and strict PII filters operating | Application Layer |
| **4** | Constrained Generation | Constrained LLM + egress sentence/citation validator | Generation Layer |
| **5** | Presentation UI | Minimal Groww-inspired Chat UI + disclaimer banner | Presentation Layer |
| **6** | Hardening & Tuning | Validated system, under 50MB RAM usage, ready for launch | Security & Non-Functional |

---

## 🛠️ Detailed Phase Breakdown

### Phase 0: Setup & Foundation
* **Goal**: Establish the repository framework, package configurations, and core directory conventions.
* **Tasks**:
  * Initialize the workspace directory structure.
  * Define `requirements.txt` incorporating `fastapi`, `uvicorn`, `sentence-transformers`, `chromadb`, and `pydantic`.
  * Establish a centralized `.env` framework managing the `GROQ_API_KEY`, API port allocations, and update timestamps.
* **Verification**:
  * Run a skeleton FastAPI endpoint (`/health`) successfully on port 8000.

---

### Phase 1: Offline Ingestion Pipeline
* **Goal**: Build the daily crawler, HTML section cleaner, text chunker, and embedding generator.
* **Tasks**:
  * **Crawler**: Fetch content from the 17 verified HDFC URLs.
  * **Cleaner/Parser**: Strip generic layout grids (header, footer, cookie popups). Decode unicode entities and normalize white space.
  * **Chunker**: Integrate a **Recursive Character Text Splitter** with a chunk size of `384` characters and an overlap of `80`, using hierarchical separators `["\n\n", "\n", ". ", " ", ""]` to prevent splitting table rows/lists, and prepend scheme name context to each chunk.
  * **Embeddings**: Initialize local sentence encoders (`BAAI/bge-small-en-v1.5`) to translate chunk paragraphs to numerical vector arrays.
  * **Daily Scheduler**: Configure a local cron worker running statefully to re-index daily at 10:00 AM and record the update date.
* **Verification**:
  * Write a pipeline test verifying that scraped, chunked text is successfully converted into vector points and saved to the index database.

---

### Phase 2: Semantic Retrieval Layer
* **Goal**: Enable vector database search matching user queries to relevant HDFC text chunks.
* **Tasks**:
  * Establish vector indexes (ChromaDB) operating locally inside the server workspace, strictly matching the **under 50MB RAM limit**.
  * Construct a semantic search helper retrieving the top-K chunks and matching source URL metadata.
  * Set up metadata filtering criteria to assure search queries only match relevant documents.
* **Verification**:
  * Query: *"HDFC Small Cap exit load"* successfully retrieves chunks from `explore/mutual-funds/hdfc-small-cap-fund/direct` with a confidence score above 0.7.

---

### Phase 3: Ingress Query Classifier & Compliance Gate
* **Goal**: Build the PII detector and advisory refusal router.
* **Tasks**:
  * **PII Detector**: Set up regular expressions (regex) scanning for PAN, Aadhaar, credit card patterns, and email signatures.
  * **Query Classifier**: Implement a fast keyword match combined with a zero-shot classification router sorting inputs into:
    * `Factual` (routes to semantic retriever).
    * `Advisory / Comparison` (routes to Refusal Handler).
  * **Refusal Handler**: Pre-compile standard polite refusals pointing to AMFI/SEBI educational pages.
* **Verification**:
  * Query *"Should I buy HDFC Large Cap?"* returns a polite refusal and AMFI link in under 100ms without hitting the vector DB or LLM APIs.
  * Query *"PAN number is ABCDE1234F"* drops immediately with a privacy warnings banner.

---

### Phase 4: Constrained Generation & Egress Gate
* **Goal**: Integrate the Groq LLM API and implement output validators.
* **Tasks**:
  * Establish Groq client connections leveraging constrained system prompts.
  * **Length Guard**: Post-process generated outputs, splitting strings into sentences and truncating everything beyond sentence 3.
  * **Citation Validator**: Scans the egress content to verify that exactly **one citation link** matches the retrieved HDFC source URL.
  * **Footer Ingest**: Concatenate the crawler's index update date to output footers: `"Last updated from sources: <date>"`.
* **Verification**:
  * Check that queries return exactly 1 cited source URL, have no advisory leakage, are under 3 sentences, and display the update date footer.

---

### Phase 5: Groww-Inspired Presentation Layer
* **Goal**: Build a minimal, responsive Web UI featuring Groww design accents.
* **Tasks**:
  * Build a single-page chat UI using standard HTML, CSS, and JS.
  * Apply a sleek design system with curated Groww color harmonies (Mint Green, Deep Space Dark Mode).
  * Feature three factual preset prompt buttons (e.g., *"What is HDFC Mid-Cap exit load?"*).
  * Place a highly visible disclaimer banner: `"Facts-only. No investment advice."`
* **Verification**:
  * Open in a browser to check visual rendering, responsive resizing on mobile dimensions, and smooth transitions when query responses load.

---

### Phase 6: Hardening, Optimization & Launch
* **Goal**: Verify end-to-end security, benchmark latencies, and check production parameters.
* **Tasks**:
  * Perform RAM profile testing to verify the backend operates cleanly within a **512MB RAM budget**.
  * Verify that under concurrent queries, latencies remain below 1.5 seconds.
  * Clean up temporary ingestion logs and compile the deployment README.
* **Verification**:
  * Execute comprehensive integration tests ensuring all success criteria in the problem statement are met.

---

## 🔒 Definition of Done (DoD)

The project is considered complete when:
1. **Source Grounding**: 100% of non-refused answers are verified against and cited from the 17 official HDFC Mutual Fund pages.
2. **Strict Refusals**: Advisory, rating, and returns-comparison inputs are gracefully intercepted and rejected.
3. **Format Bound**: No response contains more than 3 sentences or lacks a single verified citation URL and timestamp footer.
4. **Data Privacy**: Input logs contain zero traces of sensitive user PII.
5. **Aesthetics & Performance**: A clean, Groww-inspired UI serves responses with average query response latency under 1.5 seconds on 512MB RAM budgets.
