"""
Unit Tests for System Component Health Checker
==============================================

This test suite verifies component diagnostics and health status reports:
- `test_health_checker_initialization`: checks initialization of Ollama URLs and models.
- `test_health_checker_status_info`: checks health check results structure.
- `test_check_qdrant_and_n8n_response_format`: checks response shapes for Qdrant and n8n services.
"""
import pytest
from src.health_checker import OllamaHealthChecker

def test_health_checker_initialization():
    checker = OllamaHealthChecker("http://localhost:11434", "llama3.2:1b")
    assert checker.base_url == "http://localhost:11434"
    assert checker.model_name == "llama3.2:1b"
    assert isinstance(checker.is_available, bool)

def test_health_checker_status_info():
    checker = OllamaHealthChecker()
    info = checker.get_status_info()
    assert "status" in info
    assert "model" in info
    assert "base_url" in info
    assert "healthy" in info
    assert "infrastructure" in info
    assert "qdrant" in info["infrastructure"]
    assert "n8n" in info["infrastructure"]

def test_check_qdrant_and_n8n_response_format():
    checker = OllamaHealthChecker()
    qdrant_info = checker.check_qdrant()
    assert "status" in qdrant_info
    assert "url" in qdrant_info

    n8n_info = checker.check_n8n()
    assert "status" in n8n_info
    assert "url" in n8n_info
