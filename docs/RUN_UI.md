# Smart Loan Rate Advisor 🇦🇺 — Web UI & Visual Inspection Guide

This document provides a comprehensive step-by-step guide for testing, inspecting, and validating the **Smart Loan Rate Advisor** Web UI workflow across all 4 system architecture components.

---

## 🏛️ 1. Architecture Overview & Endpoints

| Component | Service | Local Endpoint / URL | Purpose |
| :--- | :--- | :--- | :--- |
| **1. Web Dashboard** | Python Flask (`dashboard/server.py`) | [http://localhost:8000](http://localhost:8000) | Main Glassmorphic Web UI & API server |
| **2. LLM Engine** | Ollama (`llama3.2:1b`) | [http://localhost:11434](http://localhost:11434) | Local LLM text generation & embeddings |
| **3. Vector Database** | Qdrant (Docker Container) | [http://localhost:6333/dashboard](http://localhost:6333/dashboard) | Vector store & similarity search UI |
| **4. Automation Engine** | n8n (Docker Container) | [http://localhost:5678](http://localhost:5678) | Visual RAG workflow orchestrator |

---

## ⚙️ 2. One-Time Setup & Vector Database Initialization

Before running the workflow, configure your environment and initialize your vector collection:

### Step 0: Configure Environment Variables
Copy `.env.example` to `.env` for local testing/development:
```bash
cp .env.example .env
```

### Step 1: Pull LLM & Embedding Models in Ollama
```bash
# Pull LLM generation model
ollama pull llama3.2:1b

# Pull dedicated vector embedding model (required for Qdrant RAG)
ollama pull nomic-embed-text
```

### Step 2: Initialize Qdrant Collection (`loan_advisor_rag`)
Create the `loan_advisor_rag` vector collection with vector size `768` (matching `nomic-embed-text` output):
```bash
curl -X PUT http://localhost:6333/collections/loan_advisor_rag \
  -H "Content-Type: application/json" \
  -d '{"vectors": {"size": 768, "distance": "Cosine"}}'
```

### Step 3: Connect & Configure n8n Workflows
1. Open n8n UI at **[http://localhost:5678/home/workflows](http://localhost:5678/home/workflows)**
2. Click **`Add workflow`** > **`Import from file`**:
   - Select `n8n_workflows/1_data_ingestion_workflow.json`.
   - **Fix Qdrant Credentials**: Double-click **Qdrant Vector Store** -> click **Credential to connect with** -> select **Create new credential** -> set **Qdrant Server URL** to `http://host.docker.internal:6333` and leave API key blank -> click **Save**.
   - **Configure Embeddings**: Double-click **Embeddings Ollama** -> ensure model is `nomic-embed-text` and Base URL is `http://host.docker.internal:11434`.
   - Click **Save** in top right & **Test Workflow** (populates ~15–20 vector points into Qdrant!).
3. Import **Workflow 2**:
   - Select `n8n_workflows/2_retrieval_rag_chain_workflow.json`.
   - Verify **Ollama LLM** URL is `http://host.docker.internal:11434/api/generate` with model `llama3.2:1b`.
   - Click **Save** and toggle top-right switch to **Active**.

---

## 🚀 3. Pre-Flight Service Status Verification

Verify all background services before launching the dashboard:

```bash
# 1. Verify Ollama LLM & Embedding Models
curl -s http://localhost:11434/api/tags

# 2. Verify Qdrant Vector Collection (status: "green")
curl -s http://localhost:6333/collections/loan_advisor_rag

# 3. Verify n8n Automation Engine (note the trailing 'z': /healthz)
curl -s http://localhost:5678/healthz

# 4. Verify Web Dashboard Backend Status (/api/health or /health)
curl -s http://localhost:8000/api/health
```

> [!NOTE]
> **Health Check Route Note**: The n8n container uses the Kubernetes standard `/healthz` probe endpoint with a `z`. Querying `/health` against n8n returns a 404 error. The Python Web Dashboard uses `/api/health`.

---

## 🖥️ 4. Web Dashboard Step-by-Step UI Demo Flow

Open your web browser at 👉 **[http://localhost:8000](http://localhost:8000)**

### Step 1: Check Connection Status Badges
- Observe the top sidebar status indicators:
  - **Ollama Status**: Green badge showing `llama3.2:1b` connected.
  - **System Connection Badges**: Validated status for Qdrant (`:6333`) and n8n (`:5678`).

### Step 2: Interactive Query Submission (`Loan Rate Advisor` Tab)
1. Select the **Loan Rate Advisor** tab.
2. Enter sample query: *"Should I lock in at 5.2% given current market conditions?"*
3. Click **Analyze Rates & Guardrails**.
4. Review the output payload:
   - **Market Context**: RBA Official Cash Rate (4.35%) & 12m projection (3.85%).
   - **Sentiment Indicator**: Rate cut likelihood (62%).
   - **Open Banking MCP Comparison Table**: Top bank rates (Alpha 4.60%, Beta 4.65%, Omega 4.75%).
   - **RAGAS Evaluation Cards**: Answer Relevance (0.90), Context Relevance (0.75), Faithfulness (0.91).
   - **3-Layer Guardrail Badges**: ✅ Fact-Check, ✅ Confidence Threshold ≥ 0.70, ✅ Licensed Financial Broker Disclaimer.

### Step 3: Complementary UI Tabs
- **RBA & Market Signals**: Macro economic indicators and rate projections.
- **Guardrails Before/After**: Compare unguarded LLM responses vs guardrail-enforced outputs.
- **Audit Alert Logs**: Live table of recent evaluation decisions and pass rates.
- **Configuration**: System parameters, active models, and execution modes.

---

## 📊 5. Component Dashboards & Vector Inspection

Inspect system components visually in your browser:

1. **Qdrant Vector Database Dashboard**:
   - URL: 👉 [http://localhost:6333/dashboard#/collections](http://localhost:6333/dashboard#/collections)
   - Action: Click on `loan_advisor_rag` collection. View point count (20 items), payload JSON metadata (RBA rates, CDR customer profile, bank loans), and inspect the 768-length vector embedding arrays.

2. **n8n Automation Engine UI**:
   - URL: 👉 [http://localhost:5678/home/workflows](http://localhost:5678/home/workflows)
   - Action: Inspect execution traces for `1. Smart Loan Advisor - Data Ingestion` and `2. Smart Loan Advisor - Retrieval RAG Chain`.

3. **Ollama LLM Engine API**:
   - URL: 👉 [http://localhost:11434/api/tags](http://localhost:11434/api/tags)
   - Action: Verify loaded models (`llama3.2:1b` and `nomic-embed-text`).

---

## 🔍 6. Log Files & Audit Inspection

Inspect backend runtime logs directly from your terminal:

```bash
# View recent JSON guardrail decisions and RAGAS scores
tail -n 20 logs/guardrails_alerts.json

# View detailed pipeline execution traces and MCP tool calls
tail -n 50 logs/pipeline_execution.log

# Verify vector collection index status
curl -s http://localhost:6333/collections/loan_advisor_rag | jq .
```
---

## 🛠️ Troubleshooting & Setup Fixes

For common connection errors, model compatibility issues, or Qdrant collection missing errors, please refer to the dedicated [Troubleshooting Guide](TROUBLESHOOTING.md).
