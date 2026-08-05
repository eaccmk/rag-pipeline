"""
Unit Tests for Flask Dashboard API Server
=========================================

This test suite verifies the endpoint responses and payload formats for the Flask server:
- `/api/health`: checks system health and infrastructure availability indicators.
- `/api/config`: checks active configuration settings (Ollama model, Qdrant host, etc.).
- `/api/market_data`: checks Reserve Bank of Australia (RBA) cash rates and market sentiments.
- `/api/mcp/business-loans`: checks open banking MCP product recommendations.
- `/api/query`: checks native RAG query pipeline execution, validation, and evaluations.
"""
import pytest
from dashboard.server import app

@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client

def test_api_health(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.get_json()
    assert "status" in data
    assert "healthy" in data
    assert "infrastructure" in data

def test_api_config(client):
    response = client.get("/api/config")
    assert response.status_code == 200
    data = response.get_json()
    assert "ollama_model" in data
    assert "use_n8n_pipeline" in data
    assert "qdrant_host" in data

def test_api_market_data(client):
    response = client.get("/api/market_data")
    assert response.status_code == 200
    data = response.get_json()
    assert "rba" in data
    assert "sentiment" in data
    assert "customer" in data
    assert "top_business_loans" in data

def test_api_mcp_business_loans(client):
    response = client.get("/api/mcp/business-loans")
    assert response.status_code == 200
    data = response.get_json()
    assert data["mcp_server"] == "open-banking-mcp"
    assert data["tool_called"] == "list_banking_products"
    assert len(data["top_recommendations"]) > 0

def test_api_query_python_native(client):
    response = client.post("/api/query", json={
        "query": "Should I lock in at 5.2% given current market conditions?",
        "customer_id": "CUST_001",
        "use_n8n": False
    })
    assert response.status_code == 200
    data = response.get_json()
    assert "query" in data
    assert "answer" in data
    assert "confidence" in data
    assert "validation" in data
    assert "ragas_metrics" in data
