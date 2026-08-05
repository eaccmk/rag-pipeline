# Smart Loan Rate Advisor - Local n8n RAG Setup Guide

This guide details how to import, configure, and run the local **n8n** automation workflows for the RAG pipeline.

---

## 🚀 1. Import n8n Workflows

In case your n8n is not up, run `docker compose up` from the root or directly run this command to start n8n:
```bash
docker run -d --name n8n_automation -p 5678:5678 -v n8n_data:/home/node/.n8n n8nio/n8n:latest
```

Open your n8n UI at **`http://localhost:5678`**:

1. **Workflow 1 (Data Ingestion)**:
   - Click **Workflows** > **Import from file**.
   - Select `n8n_workflows/1_data_ingestion_workflow.json`.
   - This workflow fetches CDR bank data and indexes it into Qdrant.

2. **Workflow 2 (RAG Chain)**:
   - Click **Workflows** > **Import from file**.
   - Select `n8n_workflows/2_retrieval_rag_chain_workflow.json` or `n8n_workflows/2_retrieval_rag_chain_workflow_2.json`.
   - Once imported, toggle the top-right switch to **Active**.

---

## ⚙️ 2. Workflow & Node Configuration

### Workflow 1: Data Ingestion & Indexing
- **Source Endpoint**: `GET http://host.docker.internal:8000/api/market_data`
- **Text Splitter**: Chunk Size: `500`, Chunk Overlap: `100`
- **Embeddings Ollama**: Base URL: `http://host.docker.internal:11434`, Model: `nomic-embed-text`
- **Qdrant Vector Store**: URL: `http://host.docker.internal:6333`, Collection: `loan_advisor_rag`

### Workflow 2: Retrieval & RAG Chain
- **Webhook Trigger**: `POST http://localhost:5678/webhook/loan-advisor-query`
- **Ollama LLM Node**: Base URL: `http://host.docker.internal:11434`, Model: `llama3.2:1b`
- **Guardrails Node**: Validates criteria (confidence ≥ 0.70, safety) and formats the final JSON payload.

---

## 🧪 3. Testing n8n Execution

### 1. Ingestion Run
- Click **Test Workflow** inside the Data Ingestion workflow to trigger index creation and vector population in Qdrant.
- Verify that vectors are populated by opening the Qdrant Dashboard in your browser at: **`http://localhost:6333/dashboard`**

### 2. Querying the Webhook
You can query the RAG retrieval chain directly via `curl`:
```bash
curl -X POST http://localhost:5678/webhook/loan-advisor-query \
  -H "Content-Type: application/json" \
  -d '{"query": "Should I lock in at 5.2% given current market conditions?", "customer_id": "CUST_001"}'
```
