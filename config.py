import os
from dotenv import load_dotenv
from pathlib import Path

# Project Paths
BASE_DIR = Path(__file__).resolve().parent

# Check for .env file presence
env_file = BASE_DIR / ".env"
if not env_file.exists():
    print("\033[91m⚠️ ERROR: .env configuration file is missing! Please copy .env.example to .env to configure local settings. Using default environment settings.\033[0m")

load_dotenv()
DATA_DIR = BASE_DIR / "data"
LOGS_DIR = BASE_DIR / "logs"
DASHBOARD_DIR = BASE_DIR / "dashboard"

# Ensure directories exist
LOGS_DIR.mkdir(exist_ok=True)
DATA_DIR.mkdir(exist_ok=True)
DASHBOARD_DIR.mkdir(exist_ok=True)

# Ollama Configuration
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2:1b")

# Validate model format
if ':' not in OLLAMA_MODEL:
    OLLAMA_MODEL = f"{OLLAMA_MODEL}:latest"

# API Configuration
MCP_SERVER_URL = os.getenv("MCP_SERVER_URL", "http://localhost:8000")
MCP_AUTH_TOKEN = os.getenv("MCP_AUTH_TOKEN", "")

# Application Configuration
APP_ENV = os.getenv("APP_ENV", "development")
DEBUG = os.getenv("DEBUG", "True").lower() == "true"
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
EXECUTION_MODE = os.getenv("EXECUTION_MODE", "local")
USE_MOCK_DATA = os.getenv("USE_MOCK_DATA", "False").lower() == "true"
DEFAULT_THEME = os.getenv("DEFAULT_THEME", "dark")

# Guardrails Configuration
CONFIDENCE_THRESHOLD = float(os.getenv("CONFIDENCE_THRESHOLD", "0.7"))
FACT_CHECK_ENABLED = os.getenv("FACT_CHECK_ENABLED", "True").lower() == "true"
DISCLAIMER_REQUIRED = os.getenv("DISCLAIMER_REQUIRED", "True").lower() == "true"

# Dashboard Configuration
DASHBOARD_PORT = int(os.getenv("DASHBOARD_PORT", "8000"))
DASHBOARD_HOST = os.getenv("DASHBOARD_HOST", "0.0.0.0")

# Vector Store & Database Configuration
QDRANT_HOST = os.getenv("QDRANT_HOST", "localhost")
QDRANT_PORT = int(os.getenv("QDRANT_PORT", "6333"))
QDRANT_COLLECTION = os.getenv("QDRANT_COLLECTION", "loan_advisor_rag")

# n8n Workflow Integration
N8N_BASE_URL = os.getenv("N8N_BASE_URL", "http://localhost:5678")
N8N_WEBHOOK_URL = os.getenv("N8N_WEBHOOK_URL", "http://localhost:5678/webhook/loan-advisor-query")
USE_N8N_PIPELINE = os.getenv("USE_N8N_PIPELINE", "False").lower() == "true"

# RAG Configuration
RAG_CHUNK_SIZE = 500
RAG_CHUNK_OVERLAP = 100
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "llama3.2:1b")



# Logging Configuration
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
GUARDRAILS_LOG_FILE = LOGS_DIR / "guardrails_alerts.json"
PIPELINE_LOG_FILE = LOGS_DIR / "pipeline_execution.log"

if __name__ == "__main__":
    print(f"Base Directory: {BASE_DIR}")
    print(f"Ollama Model: {OLLAMA_MODEL}")
    print(f"Confidence Threshold: {CONFIDENCE_THRESHOLD}")
