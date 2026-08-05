# Smart Loan Rate Advisor 🇦🇺 — CLI Demo & Verification Script

This document serves as a step-by-step recording script for verifying and demonstrating the **Smart Loan Rate Advisor** system end-to-end via CLI and terminal commands.

---
## 🏗️ 1. Start Infrastructure & Components

### Configure Environment Variables
Copy `.env.example` to `.env` for local testing/development:
```bash
cp .env.example .env
```

### Start Core Infrastructure Services
Start the core infrastructure services (Qdrant and n8n) using Docker Compose:

```bash
docker compose up -d
```

<details>
<summary><b>Alternative: Start containers individually (expand to view)</b></summary>

### Step 1: Launch Qdrant Vector Database Container
```bash
docker run -d --name qdrant_vector_store -p 6333:6333 -p 6334:6334 -v qdrant_storage:/qdrant/storage qdrant/qdrant:latest
```

### Step 2: Launch n8n Automation Engine Container
```bash
docker pull n8nio/n8n:latest
docker run -d --name n8n_automation -p 5678:5678 -v n8n_data:/home/node/.n8n n8nio/n8n:latest
```

</details>

### Step 3: Launch Local Ollama LLM Engine
```bash
OLLAMA_HOST=0.0.0.0:11434 ollama serve && ollama run llama3.2:1b
```

### Step 4: Launch Python Web Dashboard Backend
```bash
source venv/bin/activate && python dashboard/server.py
```

---

## 🎬 2. Sequential CLI Verification Run (Demo Script)

Open a separate terminal window to execute the verification sequence:

### Command 1: Run Full Pytest Suite

```bash
source venv/bin/activate && pytest tests/ -v
```

**Expected Output like:** `18 passed in ~2 minutes`

---

### Command 2: Health Check All 4 Infrastructure Components

```bash
curl -s http://localhost:8000/api/health
```

**Expected JSON Response (200 OK):**
```json
{
  "base_url": "http://localhost:11434",
  "details": {
    "available_models": [
      "llama3.2:1b"
    ],
    "model_found": true
  },
  "healthy": true,
  "infrastructure": {
    "n8n": {
      "status": "available",
      "url": "http://localhost:5678/healthz"
    },
    "qdrant": {
      "status": "available",
      "url": "http://localhost:6333/healthz"
    }
  },
  "last_check": "2026-08-02T16:54:55.970751+00:00",
  "model": "llama3.2:1b",
  "status": "available"
}
```

---

### Command 3: Fetch Open Banking MCP Product Data

```bash
curl -s http://localhost:8000/api/mcp/business-loans
```

**Expected JSON Response:**
```json
{
  "category": "BUSINESS_LOANS",
  "mcp_server": "open-banking-mcp",
  "tool_called": "list_banking_products",
  "top_recommendations": [
    {
      "bank_id": "alpha-bank",
      "bank_name": "Alpha Bank",
      "interest_rate": 4.6,
      "link": "https://www.alphabank.example.com/",
      "product_name": "Alpha Business Loan",
      "status": "LIVE_CDR_MCP"
    },
    {
      "bank_id": "beta-bank",
      "bank_name": "Beta Bank",
      "interest_rate": 4.65,
      "link": "https://www.betabank.example.com/business-loans",
      "product_name": "Business Finance & Line of Credit",
      "status": "LIVE_CDR_MCP"
    },
    {
      "bank_id": "omega-bank",
      "bank_name": "Omega Bank",
      "interest_rate": 4.75,
      "link": "https://www.omegabank.example.com/betterbusiness-loan",
      "status": "LIVE_CDR_MCP"
    }
  ]
}
```

---

### Command 4: Execute Live RAG Query (3-Layer Guardrails & Ragas Evaluation)

```bash
curl -s -X POST http://localhost:8000/api/query \
  -H "Content-Type: application/json" \
  -d '{"query": "Should I lock in at 5.2% given current market conditions?", "customer_id": "CUST_001"}'
```

**Expected JSON Response:**
```json
{
  "query": "Should I lock in at 5.2% given current market conditions?",
  "answer": "According to RBA signals and market data, your business rate stands at 4.8%. Market expectations lean toward rate cuts...\n\n| Bank | Product | Variable Rate | Link |\n| --- | --- | --- | --- |\n| **Alpha Bank** | Alpha Business Loan | **4.60%** | [View Product](https://www.alphabank.example.com/) |\n| **Beta Bank** | Business Finance & Line of Credit | **4.65%** | [View Product](https://www.betabank.example.com/business-loans) |\n| **Omega Bank** | BetterBusiness Loan | **4.75%** | [View Product](https://www.omegabank.example.com/betterbusiness-loan) |\n\n> **Disclaimer**: It is essential to note that consulting a licensed financial advisor or mortgage broker can provide personalized advice and help you make an informed decision tailored to your specific business needs.",
  "confidence": 0.85,
  "is_valid": true,
  "validation_results": {
    "overall_pass": true,
    "confidence_check": {
      "pass": true,
      "confidence_score": 0.85,
      "threshold": 0.7
    },
    "fact_check": {
      "pass": true,
      "confidence": 0.9,
      "citations_found": true,
      "hallucinations_detected": false
    },
    "disclaimer_check": {
      "pass": true,
      "disclaimer_found": true
    }
  },
  "ragas_metrics": {
    "context_relevance": 0.75,
    "answer_relevance": 0.9,
    "faithfulness": 0.91,
    "average_score": 0.85
  },
  "executor": "python_native_rag"
}
```

---

## 🛠️ Troubleshooting & Setup Fixes

For common connection errors, model compatibility issues, or Qdrant collection missing errors, please refer to the dedicated [Troubleshooting Guide](TROUBLESHOOTING.md).
