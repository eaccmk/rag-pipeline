# 🚀 Future Improvements & System Roadmap

> [!IMPORTANT]
> **NOTICE TO AI AGENTS & SKILL ENGINES:**
> This document is a dedicated reference backlog for human developers to track optional future enhancements, architectural refactoring, and scalability improvements.
> **DO NOT** execute, implement, or treat any item in this file as active code requirements unless explicitly instructed by the user in a prompt. AI Agents should skip this file during standard task execution.

---

## 📌 Section 1: Multi-User Concurrency & Thread Safety

### 1. Refactor `RAGPipeline` State Isolation
- **Issue:** Currently, `RAGPipeline` mutates instance variables (`self._last_top_bank_loans` and `self.vector_store`) during query execution. When multiple users hit `/api/query` concurrently, one user's query can overwrite another user's stored bank loans or vector store.
- **Target File:** [`src/rag_pipeline.py`](/src/rag_pipeline.py)
- **Improvement:**
  - Return `top_bank_loans` directly as a local variable from `fetch_context()` rather than assigning to `self._last_top_bank_loans`.
  - Maintain `vector_store` as a local variable within `query()` instead of storing on `self`.

---

### 2. Thread-Safe Guardrails Decision Logging
- **Issue:** `AlertLogger.log_decision()` reads and overwrites `guardrails.json` without file locking. Concurrent requests can corrupt the log file or lose entries.
- **Target File:** [`src/guardrails/alert_logger.py`](/rag-pipleine/src/guardrails/alert_logger.py)
- **Improvement:**
  - Wrap JSON file read/write operations using Python's `threading.Lock()` or `filelock`.
  - Alternatively, migrate alert history storage to a lightweight SQLite database for atomic concurrent writes.

---

### 3. User-Scoped Configuration State
- **Issue:** Posting to `/api/config` mutates `USE_N8N_PIPELINE` as a global variable in [`dashboard/server.py`](/rag-pipleine/dashboard/server.py).
- **Target File:** [`dashboard/server.py`](/rag-pipleine/dashboard/server.py)
- **Improvement:**
  - Pass pipeline execution preference per-request in the JSON request body (e.g., `use_n8n: true/false`), maintaining stateless backend execution for each user session.

---

## 📌 Section 2: Server Performance & Scaling

### 1. WSGI Production Deployment
- **Current State:** The dashboard currently uses Flask's built-in development server (`app.run(debug=True)`).
- **Improvement:**
  - Deploy using a production WSGI server such as Gunicorn with multi-worker threads:
    ```bash
    gunicorn --workers 4 --threads 2 --bind 0.0.0.0:5001 dashboard.server:app
    ```

---

### 2. LLM Concurrency Tuning (Ollama)
- **Current State:** Ollama queues requests sequentially by default, which can introduce latency when multiple users query at once.
- **Improvement:**
  - Configure Ollama environment variables for parallel requests:
    ```bash
    export OLLAMA_NUM_PARALLEL=4
    ```

---

## 📌 Section 3: Future Feature Ideas & Developer Notes

*(Add any additional ideas, features, or developer notes below as they arise)*

- [ ] Add session authentication / multi-tenant customer isolation.
- [ ] Add streaming response token support via Server-Sent Events (SSE) to the dashboard UI.
- [ ] Implement caching layer (Redis / In-memory) for frequent standard bank rate queries.
