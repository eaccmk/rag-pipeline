# Smart Loan Rate Advisor - Troubleshooting & Setup Fixes

This guide lists common issues and resolution steps when setting up the local RAG pipeline components.

---

### Issue 1: `Couldn't connect with these settings` / Unreachable Service in n8n
- **Cause**: n8n runs inside a Docker container. `localhost` inside Docker refers to the container itself, not the Mac host machine.
- **Fix**: In n8n node configuration credentials, use Docker's host gateway URL:
  - Ollama: `http://host.docker.internal:11434`
  - Qdrant: `http://host.docker.internal:6333`
  - Dashboard APIs: `http://host.docker.internal:8000`

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
