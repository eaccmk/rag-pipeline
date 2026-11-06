# rag-pipeline

# RAG Pipeline Project: "Smart-Business Loan Rate Advisor" 📈

A production-grade local RAG pipeline built for Australian SMB owners navigating interest rate decisions (fixing vs variable rates). The system combines Consumer Data Right (CDR) banking profiles (`CUST_001`), Open Banking product recommendations (`open-banking-mcp`), Reserve Bank of Australia (RBA) cash rate signals, and financial market sentiment with strict 3-layer guardrail validations to eliminate hallucinations.

---

## Watch Live Demo on YouTube

|Demo|Walkthrough|
|:-:|:-:|
|[![Gif demo of RAG Pipeline](demo/assets/02_demo_gif.gif)](https://www.youtube.com/watch?v=mS4pmnHNEBI)|[![Gif image of RAG pipline walkthrough with slides](demo/assets/01_walkthrough.gif)](https://www.youtube.com/watch?v=mS4pmnHNEBI)|

*Click the preview image above to watch the full live demo walkthrough of this RAG Pipeline: Smart-Business Loan Rate Advisor on YouTube.*

## Big Picture Architecture

The application relies strictly on a clean **4-Component Local Architecture**:

```mermaid
graph TD
    User([SMB Loan Applicant / Web UI]) --> DASH[1. Python Web Dashboard Backend\nhttp://localhost:8000]
    
    subgraph Data Sources & Connectors
        CDR[CDR Banking MCP Connector]
        OB[open-banking-mcp Tool]
        RBA[RBA Monetary Signals Service]
        SENT[Market News Sentiment Service]
        SEARCH[DuckDuckGo News Search]
    end
    
    DASH --> CDR
    DASH --> OB
    DASH --> RBA
    DASH --> SENT
    DASH --> SEARCH
    
    DASH -- USE_N8N_PIPELINE=true --> N8N[4. n8n Automation Engine\nhttp://localhost:5678]
    DASH -- Native Pipeline --> RAG[RAG Orchestrator]
    
    RAG --> QDRANT[(3. Qdrant Vector Store Container\nhttp://localhost:6333)]
    N8N --> QDRANT
    
    RAG --> OLLAMA[2. Local Ollama LLM Engine\nllama3.2:1b @ http://localhost:11434]
    N8N --> OLLAMA
    
    RAG --> GUARD[3-Layer Guardrails Validation]
    
    GUARD --> FactCheck[Fact-Check & Citation Verifier]
    GUARD --> ConfCheck[Confidence Threshold Check >= 0.70]
    GUARD --> DiscCheck[Financial Broker Disclaimer Verifier]
    
    GUARD --> EVAL[Ragas Quality Evaluator]
    GUARD --> AUDIT[(JSON Alert Audit Log)]
    
    EVAL --> Output([Validated Guidance Response Delivered to Web UI])
```
---

## 📖 Comprehensive Guides

- **[CLI Demo & Recording Script](docs/RUN_CLI.md)**: Full step-by-step terminal execution commands, `curl` queries, and exact sample JSON outputs for recording demos.
- **[Web UI & Inspection Guide](docs/RUN_UI.md)**: Interactive web dashboard guide, status indicator checks, and log audit inspection.
- **[n8n Workflow Setup Guide](docs/n8n_setup_guide.md)**: End-to-end instructions for importing and running n8n RAG workflows with Qdrant.
- **[Architecture & Concepts Q&A Walkthrough](docs/Q_and_A_style_walkthrough.md)**: 34 foundational, big-picture, and technical Q&A pairs explaining vectors, embeddings, Qdrant, tokenization, and pipeline flow.

---

## 🛠️ Prerequisites

Before running the project locally, ensure you have the following installed on your machine:

1. **Python 3.9+**: For running the backend server and RAG pipeline (`python3` on macOS/Linux, `python` on Windows).
2. **Docker & Docker Compose**: For running Qdrant Vector Database (`:6333`) and n8n (`:5678`).
   - macOS / Windows: [Docker Desktop](https://www.docker.com/products/docker-desktop/) (with WSL 2 enabled on Windows).
   - Linux: Docker Engine & `docker-compose-plugin`.
3. **Ollama**: For running local LLM inference and embeddings (`llama3.2:1b` & `nomic-embed-text`).
   - **macOS**: `brew install ollama` or download from [ollama.com](https://ollama.com).
   - **Windows**: Download installer from [ollama.com/download/windows](https://ollama.com/download/windows) or run `winget install Ollama.Ollama`.
   - **Linux**: `curl -fsSL https://ollama.com/install.sh | sh`.
4. **Node.js & npx** *(Optional)*: Required for live stdio execution of `open-banking-mcp`. If not present, the pipeline automatically falls back to bundled mock CDR data.
   - macOS: `brew install node`
   - Windows: `winget install OpenJS.NodeJS` or download from [nodejs.org](https://nodejs.org/).

---

## 🚀 Quick Start Guide (Step-by-Step Setup)

Follow these exact steps in order for a smooth, reproducible first-time local setup:

### Step 1: Configure Environment Variables
Copy `.env.example` to create your local `.env` file:

**macOS / Linux:**
```bash
cp .env.example .env
```

**Windows (PowerShell):**
```powershell
Copy-Item .env.example .env
```

**Windows (Command Prompt):**
```cmd
copy .env.example .env
```
*(The defaults in `.env.example` are pre-configured for local development with `USE_N8N_PIPELINE=false` and default local ports).*

---

### Step 2: Create Python Virtual Environment & Install Dependencies
Create and activate an isolated Python virtual environment, then install all project requirements (including LangChain, FAISS, and Flask):

**macOS / Linux:**
```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Install requirements
pip install -r requirements.txt
```

**Windows (PowerShell):**
```powershell
# Create virtual environment
python -m venv venv

# Activate virtual environment
.\venv\Scripts\Activate.ps1

# Install requirements
pip install -r requirements.txt
```

**Windows (Command Prompt):**
```cmd
:: Create virtual environment
python -m venv venv

:: Activate virtual environment
venv\Scripts\activate.bat

:: Install requirements
pip install -r requirements.txt
```

---

### Step 3: Launch Local Ollama LLM & Embedding Models
Start the Ollama server and pull both the generation LLM and dedicated embedding model:

**macOS / Linux:**
```bash
# Start Ollama service (keep running in terminal or run as daemon)
OLLAMA_HOST=0.0.0.0:11434 ollama serve
```

**Windows (PowerShell / Command Prompt):**
```powershell
# On Windows, Ollama usually starts automatically as a system tray icon.
# To start or bind explicitly from PowerShell:
$env:OLLAMA_HOST="0.0.0.0:11434"
ollama serve
```

In a second terminal window (or once Ollama is running, works on both macOS/Linux and Windows):
```bash
# Pull local LLM generation model (~1.3 GB)
ollama pull llama3.2:1b

# Pull dedicated vector embedding model (~274 MB, required for vector similarity)
ollama pull nomic-embed-text

# Verify models are downloaded
ollama list
```

> [!TIP]
> **Running Ollama via Docker (Containerized Alternative)**:
> If you prefer running Ollama inside Docker instead of installing it locally on the host:
> ```bash
> docker run -d --name ollama -p 11434:11434 -v ollama:/root/.ollama ollama/ollama:latest
> docker exec -it ollama ollama pull llama3.2:1b
> docker exec -it ollama ollama pull nomic-embed-text
> ```
> **Connecting n8n to Ollama**:
> - If running Ollama **locally on host**: In n8n credentials, set Base URL to **`http://host.docker.internal:11434`**
> - If running Ollama **via Docker** (same network): In n8n credentials, set Base URL to **`http://ollama:11434`** (or `http://host.docker.internal:11434` with port 11434 mapped).

---

### Step 4: Launch Infrastructure Containers & Initialize Vector Database
Start the Qdrant vector database and n8n automation engine via Docker Compose:

```bash
# Launch containers in the background
docker compose up -d
```

Initialize the `loan_advisor_rag` vector collection in Qdrant (dimension size `768` matching `nomic-embed-text` output):

**macOS / Linux:**
```bash
curl -X PUT http://localhost:6333/collections/loan_advisor_rag \
  -H "Content-Type: application/json" \
  -d '{"vectors": {"size": 768, "distance": "Cosine"}}'
```

**Windows (PowerShell):**
```powershell
curl.exe -X PUT http://localhost:6333/collections/loan_advisor_rag `
  -H "Content-Type: application/json" `
  -d '{\"vectors\": {\"size\": 768, \"distance\": \"Cosine\"}}'
```

**Windows (Command Prompt):**
```cmd
curl.exe -X PUT http://localhost:6333/collections/loan_advisor_rag -H "Content-Type: application/json" -d "{\"vectors\": {\"size\": 768, \"distance\": \"Cosine\"}}"
```

---

### Step 5: Run the Pipeline Locally

You can run and test the pipeline in three ways:

#### Option A: Direct CLI Execution
Execute an end-to-end RAG query directly in the terminal:

- **macOS / Linux**: `source venv/bin/activate && python src/rag_pipeline.py`
- **Windows (PowerShell)**: `.\venv\Scripts\Activate.ps1; python src\rag_pipeline.py`
- **Windows (CMD)**: `venv\Scripts\activate.bat && python src\rag_pipeline.py`

#### Option B: Run Automated Pytest Suite
Run the full 19-test unit and integration test suite:

- **macOS / Linux**: `source venv/bin/activate && pytest tests/ -v`
- **Windows (PowerShell)**: `.\venv\Scripts\Activate.ps1; pytest tests/ -v`
- **Windows (CMD)**: `venv\Scripts\activate.bat && pytest tests/ -v`

#### Option C: Launch Interactive Web Dashboard & Eval Suite
Start the local Flask dashboard backend:

- **macOS / Linux**: `source venv/bin/activate && python dashboard/server.py`
- **Windows (PowerShell)**: `.\venv\Scripts\Activate.ps1; python dashboard\server.py`
- **Windows (CMD)**: `venv\Scripts\activate.bat && python dashboard\server.py`

Open **[http://localhost:8000](http://localhost:8000)** in your browser to interact with the glassmorphic dashboard, query loan rates, and inspect 3-layer guardrail validations in real time.

You can also trigger the automated RAG evaluation suite at any time:
```bash
curl -s http://localhost:8000/api/eval | jq .
```

---

## 🌐 Final Setup Verification Table

Once all services are started, verify that all 4 local architecture components are active and healthy:

| Component | Web UI / Dashboard Link | API / Health Check Link | Status |
|---|---|---|---|
| **1. Web Dashboard** | [http://localhost:8000](http://localhost:8000) | [http://localhost:8000/api/health](http://localhost:8000/api/health) | 🟢 Running & Active |
| **2. Qdrant Vector DB** | [http://localhost:6333/dashboard](http://localhost:6333/dashboard) | [http://localhost:6333/collections/loan_advisor_rag](http://localhost:6333/collections/loan_advisor_rag) | 🟢 `loan_advisor_rag` (768-dim) Ready |
| **3. n8n Automation Engine** | [http://localhost:5678](http://localhost:5678) | [http://localhost:5678/healthz](http://localhost:5678/healthz) | 🟢 Workflow Engine Ready |
| **4. Ollama Local LLM** | [http://localhost:11434](http://localhost:11434) | [http://localhost:11434/api/tags](http://localhost:11434/api/tags) | 🟢 `llama3.2:1b` & `nomic-embed-text` Loaded |

> [!NOTE]
> **Health Endpoint Naming Conventions**:
> - **n8n Automation Engine** explicitly uses the Kubernetes probe convention **`/healthz`** (with a trailing `z`). Querying `/health` without `z` will return a 404 from n8n.
> - **Web Dashboard** uses standard **`/api/health`** (or `/health`).
> - **Qdrant Vector Database** verifies via its collection status endpoint **`/collections/loan_advisor_rag`** or root **`/`**.
> - **Ollama LLM Engine** verifies via the model catalog endpoint **`/api/tags`**.

### Verification Terminal Commands

```bash
# 1. Verify Web Dashboard API
curl -s http://localhost:8000/api/health

# 2. Verify Qdrant Vector Collection (status: "green")
curl -s http://localhost:6333/collections/loan_advisor_rag

# 3. Verify n8n Automation Engine (returns: {"status":"ok"})
curl -s http://localhost:5678/healthz

# 4. Verify Local Ollama Models (llama3.2:1b & nomic-embed-text)
curl -s http://localhost:11434/api/tags
```

---

## 📁 Repository Directory Structure

```
├── README.md                           <-- Main Project Overview & Architecture Guide
├── config.py                           <-- Centralized Configuration & Environment Loader
├── requirements.txt                    <-- Python Package Dependencies
├── docker-compose.yml                  <-- Qdrant & n8n Service Definition
├── .env.example                        <-- Clean Example Environment File
├── dashboard/
│   ├── server.py                       <-- Flask REST API & Web Server
│   ├── index.html                      <-- Glassmorphic Dashboard UI
│   ├── app.js                          <-- Frontend Interactions & Event Handlers
│   └── style.css                       <-- Dual Theme Styles (Dark & Light Mode)
├── src/
│   ├── rag_pipeline.py                 <-- Core RAG Orchestrator & LLM Inference
│   ├── health_checker.py               <-- Diagnostics for Ollama, Qdrant & n8n
│   ├── evaluator.py                    <-- Ragas Evaluation & Metrics
│   ├── guardrails/                     <-- 3-Layer Guardrails (Fact-Check, Confidence, Disclaimer)
│   └── data_sources/                   <-- CDR MCP, open-banking-mcp, RBA & Sentiment Services
├── tests/                              <-- 19 End-to-End Automated Test Cases
├── docs/
│   ├── RUN_CLI.md                      <-- Dedicated CLI Demo & Recording Script
│   ├── RUN_UI.md                       <-- Dedicated Web UI & Inspection Guide
│   ├── n8n_setup_guide.md              <-- n8n Workflow Import & Node Configuration
│   ├── TROUBLESHOOTING.md              <-- Connection & Setup Troubleshoot Guide
│   └── Q_and_A_style_walkthrough.md    <-- 34 In-depth Architectural & Conceptual Q&As
├── n8n_workflows/
│   ├── 1_data_ingestion_workflow.json  <-- n8n Vector Ingestion Workflow (Base)
│   ├── 1.1_data_ingestion_workflow_with_evals.json <-- Ingestion + Automated Eval Suite Hook
│   ├── 2_retrieval_rag_chain_workflow.json <-- Primary RAG Retrieval Chain
│   ├── 2_retrieval_rag_chain_workflow_2.json <-- Retrieval RAG Chain (Visual Layout)
│   └── 2.2_retrieval_rag_chain_workflow_with_evals.json <-- Retrieval Chain + Live Post-Chat Evals
├── data/                               <-- Bundled Customer Profiles & Financial Datasets
└── logs/                               <-- Guardrails Decision Audit & System Logs
```

---

## 🔒 Disclaimer
This software is provided for educational and decision support purposes only. It does not constitute personal financial product advice. Always consult a licensed mortgage broker or financial advisor before committing to loan rate modifications.
