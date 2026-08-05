import logging
import requests
from datetime import datetime, timezone
from typing import Dict, Any

logger = logging.getLogger(__name__)

class OllamaHealthChecker:
    """Monitor connectivity and health status across Ollama, Qdrant, and n8n services."""
    
    def __init__(self, base_url: str = "http://localhost:11434", model_name: str = "llama3.2:1b"):
        self.base_url = base_url.rstrip("/")
        self.model_name = model_name
        self.status = "unknown"  # 'unknown', 'available', 'unavailable'
        self.error_message = None
        self.last_check = None
        self.details = {}
        self.check_connection()
        
    @property
    def is_available(self) -> bool:
        return self.status == "available"

    def check_connection(self) -> bool:
        """Check connection to Ollama LLM server."""
        info = self.check_health()
        return self.is_available

    def check_health(self) -> Dict[str, Any]:
        """Check Ollama service connectivity and model availability."""
        self.last_check = datetime.now(timezone.utc).isoformat()
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=3)
            if response.status_code == 200:
                models_data = response.json().get("models", [])
                available_models = [m.get("name") for m in models_data]
                
                model_base = self.model_name.split(":")[0]
                has_model = any(self.model_name in m or model_base in m for m in available_models)
                
                self.status = "available"
                self.error_message = None
                self.details = {
                    "available_models": available_models,
                    "model_found": has_model
                }
                logger.info(f"Ollama health check OK. Status: available. Models: {available_models}")
            else:
                self.status = "unavailable"
                self.error_message = f"HTTP {response.status_code}"
                self.details = {"error": self.error_message}
                logger.warning(f"Ollama health check failed with HTTP {response.status_code}")
        except Exception as e:
            self.status = "unavailable"
            self.error_message = str(e)
            self.details = {"error": str(e)}
            logger.warning(f"Ollama connection error: {e}")
            
        return self.get_status_info()

    def is_healthy(self) -> bool:
        return self.status == "available"

    def get_status_info(self) -> Dict[str, Any]:
        return {
            "status": self.status,
            "model": self.model_name,
            "base_url": self.base_url,
            "last_check": self.last_check,
            "healthy": self.is_healthy(),
            "details": self.details,
            "infrastructure": {
                "qdrant": self.check_qdrant(),
                "n8n": self.check_n8n()
            }
        }

    def check_qdrant(self) -> Dict[str, Any]:
        from config import QDRANT_HOST, QDRANT_PORT
        url = f"http://{QDRANT_HOST}:{QDRANT_PORT}/healthz"
        try:
            r = requests.get(url, timeout=2)
            return {"status": "available" if r.status_code == 200 else "unavailable", "url": url}
        except Exception as e:
            return {"status": "unavailable", "url": url, "error": str(e)}

    def check_n8n(self) -> Dict[str, Any]:
        from config import N8N_BASE_URL
        url = f"{N8N_BASE_URL}/healthz"
        try:
            r = requests.get(url, timeout=2)
            return {"status": "available" if r.status_code == 200 else "unavailable", "url": url}
        except Exception as e:
            return {"status": "unavailable", "url": url, "error": str(e)}


