"""
Unit Tests for Guardrail Edge Cases & Failures
==============================================

This test suite verifies how the guardrails and connectors behave under failing conditions:
- Checks that outputs lacking the advisor/broker disclaimer fail the disclaimer guardrail.
- Checks that low confidence generations (below threshold) fail validation.
- Checks that hallucinated rate projections fail the fact-check validator.
- Checks that MCP connector falls back cleanly when queried with invalid customer IDs.
"""
import pytest
from src.guardrails.validators import GuardrailsValidator
from src.data_sources import MCPConnector

def test_missing_disclaimer_fails():
    validator = GuardrailsValidator()
    # Missing consultant/advisor disclaimer keyword
    answer = "According to data, the current rate is 4.8% and cash rate is 4.35%. You must lock in right now."
    sources = ["RBA Data"]
    
    is_valid, results = validator.validate(answer, 0.85, sources)
    assert is_valid is False
    assert results["disclaimer_check"]["pass"] is False

def test_low_confidence_fails():
    validator = GuardrailsValidator()
    answer = "According to market data, consult your financial advisor."
    sources = ["RBA Data"]
    
    # Confidence below 0.7 threshold
    is_valid, results = validator.validate(answer, 0.50, sources)
    assert is_valid is False
    assert results["confidence_check"]["pass"] is False

def test_hallucination_fails():
    validator = GuardrailsValidator()
    answer = "According to signals, interest rates will definitely drop by 3.0% next week 100% sure. Consult your broker."
    sources = ["RBA Data"]
    
    is_valid, results = validator.validate(answer, 0.85, sources)
    assert is_valid is False
    assert results["fact_check"]["pass"] is False

def test_mcp_invalid_customer_fallback():
    mcp = MCPConnector()
    data = mcp.get_customer_loans("NON_EXISTENT_ID")
    assert "loans" in data or "customer_id" in data
