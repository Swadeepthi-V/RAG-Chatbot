# Mutual Fund FAQ Assistant (Groww Context)

An AI-powered, facts-only FAQ assistant for **HDFC Mutual Fund** schemes. Built with a Retrieval-Augmented Generation (RAG) architecture, this assistant ensures retail investors receive compliant, highly accurate, and source-backed answers to objective questions without any investment advice or subjective opinions.

---

## 🚀 Key Features

* **Strict Facts-Only Guardrails**: Polishing and filtering queries to ensure no speculative advice, returns comparison, or qualitative opinions are shared.
* **Compact, Structured Responses**: Under 3 sentences per response, strictly matching source links.
* **Interactive Disclaimer**: Persistent `"Facts-only. No investment advice."` visibility.
* **AMC Corpus Grounding**: Powered exclusively by 15 official HDFC Mutual Fund pages (no third-party blog scraping).

---

## 📂 Project Structure

```text
├── docs/
│   ├── problemStatement.md    # Core project objectives & success criteria
│   ├── problemstatement.txt   # Raw text copy of the problem statement
│   └── corpus.md              # Curated HDFC Mutual Fund AMC URL definitions
├── README.md                  # Project skeleton and architecture overview
```

---

## 🏛️ Grounding Corpus

The assistant operates exclusively on a hand-curated corpus of **15 official HDFC Mutual Fund sources**:
* **NAV & IDCW details**: [hdfcfund.com/nav-and-idcw](https://www.hdfcfund.com/nav-and-idcw)
* **Official Factsheets**: [hdfcfund.com/mutual-funds/factsheets](https://www.hdfcfund.com/mutual-funds/factsheets)
* **TER Tracking**: [hdfcfund.com/investors/total-expense-ratio](https://www.hdfcfund.com/investors/total-expense-ratio)
* *For a full detailed categorization, refer to the [Corpus Documentation](./docs/corpus.md).*

---

## 🏗️ Planned RAG Architecture

```text
┌─────────────────┐       ┌─────────────────┐       ┌─────────────────┐
│  User Query     │ ───>  │  Query Router   │ ───>  │  Vector Store   │
│                 │       │  & Compliance   │       │  (HDFC Corpus)  │
└─────────────────┘       └─────────────────┘       └────────┬────────┘
                                                             │
┌─────────────────┐       ┌─────────────────┐                │
│  Polite Refusal │ <───  │  LLM Synthesis  │ <──────────────┘
│  (For Advisory) │       │  (Facts & Urls) │
└─────────────────┘       └─────────────────┘
```

1. **Query Router**: Inspects inputs for advisory keywords (e.g., "should I buy", "which is better"). Triggers immediate refusal if detected.
2. **Context Retrieval**: Vector search extracts chunked facts from SID, KIM, and official HDFC sheets.
3. **Synthesis Engine**: Prompt-guided LLM produces concise, factual statements.
4. **Verification**: Assures exactly one citation matches the extracted source URL.

---

## ⚠️ Known Limitations & Compliance

> [!WARNING]
> **Regulatory and Security Guardrails**
> * **No Performance Returns Comparisons**: The app will only route users to official factsheets for rate-of-return queries.
> * **No PII Ingestion**: Inputs are strictly monitored. Any trace of account details, bank numbers, PAN, Aadhaar, or contact data will trigger sanitization blocks.
> * **Static Knowledge Updates**: Answers include a `"Last updated from sources: <date>"` footer to reflect the exact document compilation timestamp.

---

## ⚖️ Disclaimer

> **Facts-only. No investment advice.**  
> *All information is retrieved directly from official HDFC Mutual Fund public documents. Groww or this assistant does not guarantee future performance or recommend specific portfolios. Please consult a SEBI-registered advisor before investing.*
