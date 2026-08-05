"""
Unit Tests for End-to-End Happy Paths
=====================================

This test suite verifies successful execution flows when all components are active:
- `test_rag_pipeline_happy_path`: checks document retrieval, LLM query generation, and confidence score.
- `test_guardrails_validation_happy_path`: checks validations pass when all safety indicators are met.
- `test_evaluator_happy_path`: checks Ragas quality evaluator reports metrics.
"""
import pytest
from src.rag_pipeline import RAGPipeline
from src.guardrails.validators import GuardrailsValidator
from src.evaluator import RAGEvaluator

def test_rag_pipeline_happy_path():
    pipeline = RAGPipeline()
    query = "Should I lock in at 5.2% given current market conditions?"
    answer, sources, confidence = pipeline.query(query)
    
    assert len(answer) > 20
    assert len(sources) > 0
    assert 0.0 <= confidence <= 1.0

def test_guardrails_validation_happy_path():
    validator = GuardrailsValidator()
    answer = "According to RBA signals and market data, your current rate is 4.8%. Market expectations lean toward cuts. However, consult your advisor."
    sources = ["RBA Cash Rate 4.35%", "Market sentiment 62%"]
    
    is_valid, results = validator.validate(answer, 0.85, sources)
    assert is_valid is True
    assert results["fact_check"]["pass"] is True
    assert results["confidence_check"]["pass"] is True
    assert results["disclaimer_check"]["pass"] is True

def test_evaluator_happy_path():
    evaluator = RAGEvaluator()
    metrics = evaluator.evaluate_answer(
        query="Should I lock in at 5.2%?",
        answer="According to RBA signals, locking in offers stability. Consult your advisor.",
        sources=["RBA Rate: 4.35%"],
        ground_truth_context="RBA cash rate signals"
    )
    assert "faithfulness" in metrics
    assert "context_relevance" in metrics
    assert metrics["average_score"] >= 0.70
