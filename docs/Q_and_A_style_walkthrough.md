# Smart Loan Rate Advisor 🇦🇺 — RAG Architecture Q&A Walkthrough

This document compiles the 27 foundational and big-picture questions and answers explaining the **Smart Loan Rate Advisor** local RAG application, covering architecture, technologies, vectors, embeddings, Qdrant, and data processing workflows.

---

## 🏛️ Part 1: High-Level Vision & Architecture (Q1 – Q5)

### Q1 [BIG]: What are we building?
**Answer**: An AI-powered local RAG application that helps Australian small business owners navigate interest rates by combining open banking data, RBA signals, and 3-layer guardrails.

---

### Q2 [BIG]: Who will be able to use this once deployed to production?
**Answer**: Australian small business owners, mortgage brokers, and financial advisors seeking automated, guardrailed interest rate guidance and live market loan product comparisons.

---

### Q3 [BIG]: How will non-technical users use it?
**Answer**: Through the clean web dashboard interface. They simply type natural questions like *"Should I fix my loan?"*, and view instant rate comparisons, RBA signals, and recommendations.

---

### Q4 [BASIC]: What technologies are we using?
**Answer**:

| Technology | Purpose |
| :--- | :--- |
| **Flask (Python)** | Web Dashboard Backend & API Server |
| **Ollama** | Local LLM (`llama3.2:1b`) & Embeddings (`nomic-embed-text`) |
| **Qdrant** | Vector Store for storing & searching embeddings |
| **n8n** | Automation engine for visual RAG workflows |
| **HTML / CSS / JS** | Glassmorphic Web Dashboard UI |

---

### Q5 [BIG]: What is Ollama and how does it simplify running this RAG pipeline locally?
**Answer**: Ollama is a local AI engine that runs open-source LLMs and embedding models directly on your machine without external API keys, cloud costs, or privacy risks.

---

## 🗄️ Part 2: Vector Store & Qdrant Deep Dive (Q6 – Q14)

### Q6 [BASIC]: What is Qdrant and what exactly does it do?
**Answer**: Qdrant is a high-performance vector database. It stores numerical vector arrays (embeddings) and text payloads, instantly finding the most relevant background context matching a user's question.

---

### Q7 [BASIC]: As Qdrant is a database, can I visualize its details as tables in a Web UI, and if yes, how or where?
**Answer**: **Yes!** Open [http://localhost:6333/dashboard#/collections](http://localhost:6333/dashboard#/collections) in your browser. Click `loan_advisor_rag` to inspect all stored points, JSON text payloads, and vector arrays in a clean UI view.

---

### Q8 [BASIC]: Can I run SQL-type queries on the Qdrant database?
**Answer**: **No.** Qdrant uses REST API JSON queries instead of SQL. It performs vector similarity searches combined with payload filtering (e.g., filtering by source or metadata category).

---

### Q9 [BASIC]: Give me 2 cURL commands to list all vectors and retrieve stored points as JSON.
**Answer**:

```bash
# 1. View Collection Info & Total Vector Count
curl -s http://localhost:6333/collections/loan_advisor_rag

# 2. Retrieve Stored Points (with Payloads & Vectors)
curl -s -X POST http://localhost:6333/collections/loan_advisor_rag/points/scroll \
  -H "Content-Type: application/json" \
  -d '{"limit": 5, "with_payload": true, "with_vector": true}'
```

---

### Q10 [BIG]: What are points really? Explain like I am 5 years old.
**Answer**: Imagine a magic toy chest. A **Point** is a single box inside it containing a snippet of text (the story) and a special map coordinate (the vector) showing where it belongs!

---

### Q11 [BIG]: Give a Lego example for points instead of a toy chest.
**Answer**: A **Point** is a single Lego brick. It has a sticker with information on it (payload) and a specific shape (vector) so it snaps together with matching bricks!

---

### Q12 [BASIC]: How many vectors can we have and what can be the max and min size of a vector?
**Answer**: You can store millions of vectors in Qdrant. A vector's size (dimensions) ranges from **1** up to **65,536** numbers, determined by your embedding model (`nomic-embed-text` uses 768).

---

### Q13 [BASIC]: For `nomic-embed-text`, what will happen when vector size hits 769?
**Answer**: Qdrant will throw a **dimension mismatch error** and reject the vector. `nomic-embed-text` strictly outputs fixed 768-number arrays, which must match the collection configuration.

---

### Q14 [BASIC]: When will a dimension mismatch error happen and how can we avoid it?
**Answer**: It happens if you switch embedding models or misconfigure collection creation. Avoid it by ensuring your Qdrant collection vector size always matches your model (`768` for `nomic-embed-text`).

---

## 🧬 Part 3: Vectors vs Embeddings Explained (Q15 – Q20)

### Q15 [BIG]: That's vectors, but what are embeddings and where are they stored in our project?
**Answer**: Embeddings are numerical vector representations of text meaning. In our project, Ollama (`nomic-embed-text`) generates them, and they are stored inside the Qdrant Docker container (`qdrant_storage`).

---

### Q16 [BASIC]: Can we visualize or inspect embeddings stored inside the Qdrant Docker container (`qdrant_storage`) through any UI?
**Answer**: **Yes!** Open [http://localhost:6333/dashboard#/collections](http://localhost:6333/dashboard#/collections), click `loan_advisor_rag`, and inspect any point to view its 768-number embedding vector array and JSON payload visually in your browser.

---

### Q17 [BASIC]: What is the difference between a vector and an embedding?
**Answer**: A **vector** is the general mathematical container (a list of numbers). An **embedding** is a specific type of vector created by AI that captures the semantic meaning of text.

---

### Q18 [BIG]: Explain the difference between vector and embedding like I'm 5 with 1 Lego example and 1 real-life example.
**Answer**:
- **Lego**: A vector is an empty plastic box; an embedding is the specific Lego brick shaped like a dog inside it.
- **Real Life**: A vector is raw GPS numbers; an embedding is "your home".

---

### Q19 [BIG]: Explain in more detail: "Real Life: A vector is raw GPS numbers; an embedding is 'your home'."
**Answer**: GPS numbers (`-33.86, 151.20`) are raw math data (the **vector**). "Your Home" gives those numbers real human meaning (the **embedding**). AI translates text into meaningful numerical coordinates.

---

### Q20 [BIG]: Give a visual explanation from a user perspective where the user inputs an address.
**Answer**:
1. **User Types**: *"123 Main St, Sydney"* (Text Input)
2. **AI Encodes Meaning**: Captures concept *"Cozy Family House"* (**Embedding**)
3. **Database Stores Math**: `[-0.42, 0.88, 0.15, ...]` (768-number **Vector**)

---

## 🔄 Part 4: Tokenization & RAG Pipeline Execution Flow (Q21 – Q27)

### Q21 [BASIC]: Where does tokenization fit in this example, and is 768 a fixed number or can vector size be less?
**Answer**:
- **Tokenization** happens first—breaking *"123 Main St"* into word chunks (`["123", "Main", "St"]`).
- **Vector Size**: 768 depends on the model. Smaller models use 384; larger ones use 1536+.

---

### Q22 [BASIC]: Visualize tokenization, embeddings, and vectorization using the same address example.
**Answer**:
1. **Text Input**: *"123 Main St"*
2. **Tokenization**: `["123", "Main", "St"]` (Word chunks)
3. **Embedding**: Concept *"Suburban Street Address"* (Semantic meaning)
4. **Vectorization**: `[0.12, -0.45, 0.89, ...]` (768 numbers)

---

### Q23 [BASIC]: Are we missing any steps before, between, or after steps 1 to 4, and what would step 5 be?
**Answer**:
- **Before Step 1**: Text Cleaning (lowercasing, stripping special characters).
- **In Between**: Token ID Mapping (converting tokens to integer IDs).
- **Step 5**: Indexing & Cosine Similarity Search in Qdrant.

---

### Q24 [BASIC]: Visualize all steps starting from a prompt like "Enter your address: 123 Main St!".
**Answer**:
**Prompt**: *"Enter your address: 123 Main St!"*

1. **Text Cleaning**: `"123 main st"` (Normalized text)
2. **Tokenization**: `["123", "main", "st"]` (Word chunks)
3. **Token ID Mapping**: `[452, 1089, 302]` (Integer IDs)
4. **Embedding**: Concept *"Suburban Address"* (Semantic context)
5. **Vectorization**: `[0.12, -0.45, ...]` (768-number Array)
6. **Qdrant Indexing**: Vector Storage & Similarity Search

---

### Q25 [BASIC]: Explain in detail with a 5yo example what happens at and after step 6.
**Answer**:
6. **Lego Shelf (Qdrant)**: Places your brick in a spot with matching color bricks.
7. **Similarity Search**: Grabs nearest neighbor bricks.
8. **LLM Storyteller**: Reads those bricks to give you your answer!

---

### Q26 [BASIC]: List all 8 steps together using 2 examples: 1 Lego and 1 Address.
**Answer**:

| Step | 📍 Address Example | 🧱 Lego Analogy |
| :--- | :--- | :--- |
| **1. User Input** | *"123 Main St!"* | Pick raw Lego piece |
| **2. Cleaning** | `"123 main st"` | Wipe dirt off Lego piece |
| **3. Tokenization** | `["123", "main", "st"]` | Separate into individual studs |
| **4. ID Mapping** | `[452, 1089, 302]` | Look up official Lego part numbers |
| **5. Embedding** | Concept: *"Suburban House"* | Mold into a specific house-shaped brick |
| **6. Vectorization** | `[0.12, -0.45, ...]` (768 numbers) | Measure exact 3D grid position numbers |
| **7. Qdrant Match** | Finds closest neighboring addresses | Snaps brick next to matching house bricks |
| **8. LLM Response** | Generates tailored rate advice | Reads matched bricks to tell the full story |

---

### Q27 [BASIC]: Where do MCP, RBA, and Web Search fit into the overall RAG architecture in reference to step 6?
**Answer**: They are **External Data Sources**. Before step 6, MCP, RBA, and Web Search fetch live ground-truth facts, convert them into text documents, and load them into Qdrant for retrieval.

---

## 🛠️ Part 5: TECHNICAL QUESTIONS (Q28 – Q32)

### Q28 [TECHNICAL]: Guardrails Validation
**Question**: How do we guarantee the AI doesn't hallucinate fake loan rates or give illegal financial advice?  
**Answer**: Through a **3-Layer Guardrail Validator**:
1. **Fact-Checker**: Cross-references claims against source documents to catch hallucinations.
2. **Confidence Threshold**: Rejects answers with confidence score < 0.70.
3. **Regulatory Disclaimer Enforcement**: Automatically verifies and appends mandatory licensed mortgage broker / financial advisor disclaimers.

---

### Q29 [TECHNICAL]: RAGAS Quality Metrics
**Question**: How do we mathematically measure if the AI's answer is good and accurate?  
**Answer**: Through **RAGAS Evaluation Metrics**:
- **Answer Relevance**: Measures how directly the response addresses the prompt.
- **Context Relevance**: Measures how much retrieved context was useful vs. noise.
- **Faithfulness**: Measures if the answer relies strictly on retrieved context without introducing external assumptions.

---

### Q30 [TECHNICAL]: MCP (Model Context Protocol) & CDR Banking Data
**Question**: What is `open-banking-mcp` and how does it fetch real Australian bank loan products?  
**Answer**: Model Context Protocol (MCP) is an open standard allowing LLMs to safely query live external tools. In our project, `open-banking-mcp` queries Australian Consumer Data Right (CDR) public banking APIs to fetch up-to-date loan products from major banks (e.g., Alpha Bank, Beta Bank, Omega Bank).

---

### Q31 [TECHNICAL]: n8n Webhook vs. Native Python Pipeline
**Question**: What is the difference between running queries via n8n vs. Python native backend, and why have both?  
**Answer**:
- **n8n Pipeline** (`USE_N8N_PIPELINE=true`): Provides visual, no-code workflow orchestration, ideal for debugging, non-developer customization, and third-party integrations.
- **Python Native Pipeline** (`server.py`): Provides low-latency, programmatic execution directly via Python code, ideal for high-throughput production API endpoints.

---

### Q32 [TECHNICAL]: Production Security & Scalability
**Question**: How do we secure user financial data when moving from local development to production deployment?  
**Answer**:
1. **Container Isolation**: Run Qdrant and n8n in restricted Docker networks.
2. **Data Privacy**: Local LLMs (`llama3.2:1b`) keep customer financial profiles completely within private infrastructure.

---

### Q33 [Y/N]: Is this project free?
**Question**: Is this project free to use and deploy?  
**Answer**: **Yes.** 100% free and open-source. It runs entirely locally using Ollama (`llama3.2:1b`), Qdrant, n8n, and Flask without requiring any cloud subscriptions or paid API keys.

---

### Q34 [Y/N]: Is this project safe to run locally?
**Question**: Is this project safe and private to run locally on your machine?  
**Answer**: **Yes.** All LLM inference, embeddings, vector storage, and guardrail checks execute completely on your machine—no sensitive financial data or customer profiles ever leave your local network.

---

### Q35 [TECHNICAL]: Guardrail Types & Implementation Library
**Question**: What are the various guardrails used in this project and which library was used?  
**Answer**: We use a custom, zero-dependency 3-Layer Guardrail validator (`src/guardrails/validators.py`) combined with RAGAS metrics (`src/evaluator.py`):
1. **Fact-Check Validator**: Verifies source citations and flags hallucination trigger phrases.
2. **Confidence Threshold Scorer**: Rejects responses with confidence < 0.70 (`CONFIDENCE_THRESHOLD`).
3. **Financial Disclaimer Verifier**: Enforces regulatory Australian mortgage broker compliance disclaimers.



