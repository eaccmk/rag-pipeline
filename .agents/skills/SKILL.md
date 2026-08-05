---
name: rag-pipeline-management
description: Guides updating, running, verifying, or debugging the RAG pipeline, Flask server, and docker compose services.
---

# 🛠️ RAG Pipeline Management Skill

This skill provides step-by-step instructions for managing and troubleshooting the local RAG pipeline application.

## 📋 Pre-requisites & Env Check
1. Always verify the presence of a `.env` file in the root. If missing, copy it from `.env.example`.
2. Do not use absolute local paths like `/Users/demo/` anywhere in tracking or documentation files.

## 🚀 Running the System
* **Infrastructure**: Run `docker compose up -d` to launch Qdrant and n8n services.
* **Backend Flask server**: Run `python dashboard/server.py` in the activated virtual environment (`venv`).
* **Local models**: Run `ollama run llama3.2:1b` and `ollama pull nomic-embed-text`.

## 🧪 Testing and Verification
* Run unit tests: `pytest tests/ -v`
* Verify n8n webhook:
  ```bash
  curl -X POST http://localhost:5678/webhook/loan-advisor-query -H "Content-Type: application/json" -d '{"query": "Should I lock in at 5.2%?"}'
  ```

## 🛡️ Guardrails & Evaluations
* Guardrail validator logic is located in [validators.py](file:///Users/demo/code/learning/rag-pipleine/src/guardrails/validators.py).
* Ragas evaluation metrics calculations are in [evaluator.py](file:///Users/demo/code/learning/rag-pipleine/src/evaluator.py).
