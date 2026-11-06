# Smart Loan Rate Advisor - Troubleshooting & Setup Fixes

This guide lists common issues and resolution steps when setting up the local RAG pipeline components.

---

### Issue 1: `Couldn't connect with these settings` / `ENOTFOUND ollama` in n8n
- **Cause**: 
  - Standard n8n docs suggest `http://ollama:11434`. That only works when Ollama is running inside another Docker container with the container name/alias `ollama` on the **same Docker network** as n8n.
  - If Ollama is running locally on your host machine (or if containers are not on the same Docker bridge network), n8n cannot resolve the `ollama` hostname, and `localhost` inside Docker refers to the container itself.
- **Fix**: Choose the URL matching your Ollama deployment:
  - **Running Ollama Locally on Host (Native app/CLI)**: Set Base URL to **`http://host.docker.internal:11434`**
  - **Running Ollama in Docker (Same Compose Network)**: Set Base URL to **`http://ollama:11434`**
  - **Universal Fallback (Docker with port 11434 published)**: **`http://host.docker.internal:11434`** (reaches port 11434 through Docker host gateway)
  - **Qdrant Vector Store URL**: `http://host.docker.internal:6333`
  - **Dashboard APIs URL**: `http://host.docker.internal:8000`

### Issue 2: `This server does not support embeddings` / HTTP 501 in Ollama
- **Cause**: Attempting to generate embeddings with `llama3.2:1b` (a chat LLM model) via `/api/embed` returns HTTP 501.
- **Fix**: Download the dedicated embedding model via `ollama pull nomic-embed-text` and update the **Embeddings Ollama** node model in n8n to `nomic-embed-text`.

### Issue 3: `Not found: Collection loan_advisor_rag doesn't exist!`
- **Cause**: Qdrant is running, but the collection has not been initialized.
- **Fix**: Run the cURL command:
  ```bash
  curl -X PUT http://localhost:6333/collections/loan_advisor_rag \
    -H "Content-Type: application/json" \
    -d '{"vectors": {"size": 768, "distance": "Cosine"}}'
  ```

### Issue 4: `Problem in node 'Qdrant Vector Store': Node does not have any credentials set`
- **Cause**: n8n requires an explicit Qdrant Credential object attached to the vector store node.
- **Fix**: Click on the **Qdrant Vector Store** node -> **Create New Credential** -> Set **Qdrant Server URL** to `http://host.docker.internal:6333` and leave API key blank.

### Issue 5: `Oops, couldn't find that 404 Error` when accessing n8n health check
- **Cause**: Navigating to `http://localhost:5678/health`. The n8n automation container uses the Kubernetes-standard `/healthz` probe endpoint with a trailing `z`.
- **Fix**: Use `http://localhost:5678/healthz` (which responds with `{"status":"ok"}`). The Python Web Dashboard uses standard `/api/health` or `/health`.

---

### Issue 6: `405 Method Not Allowed` in n8n on `Run RAG Evaluation Suite`
- **Cause**: The Flask dashboard server running on port 8000 (either in a Docker container or terminal) was started with older code before `/api/eval` was added. Because the route was missing in memory, Flask routed the request to its static catch-all handler (`/<path:path>`), which only permits `GET` requests.
- **Fix**: Rebuild/restart the dashboard server to load the new `/api/eval` route:
  - **If running via Docker Compose**:
    ```bash
    docker compose up -d --build
    ```
  - **If running as a standalone Docker container**:
    ```bash
    # Stop the old container holding port 8000
    docker stop $(docker ps -q --filter "publish=8000")
    # Rebuild and run with current directory mounted
    docker build -t rag-dashboard .
    docker run -d --name rag_dashboard -p 8000:8000 -v $(pwd):/app --add-host=host.docker.internal:host-gateway rag-dashboard
    ```
  - **If running natively on Host**:
    ```bash
    # Stop any Docker container on port 8000 first, then:
    python dashboard/server.py
    ```

---

### Issue 7: `socket hang up` / `ECONNRESET` in n8n on `Run RAG Evaluation Suite`
- **Cause**: By default, n8n invokes downstream nodes once per input item. When Qdrant outputs 20 chunk items, n8n attempts 20 concurrent/sequential evaluation requests, causing socket timeouts in Node.js while the local LLM evaluates multiple questions.
- **Fix**: 
  1. Add a **`Consolidate Ingestion Status`** Code node between `Qdrant Vector Store` and `Run RAG Evaluation Suite` to merge the 20 chunks into 1 single event.
  2. In the HTTP Request node options, set `"timeout": 120000` (2 minutes).
  3. Re-import [`n8n_workflows/1.1_data_ingestion_workflow_with_evals.json`](../n8n_workflows/1.1_data_ingestion_workflow_with_evals.json).
