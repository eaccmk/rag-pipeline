"""
Unit Tests for Before/After Guardrails Quality Comparison
=========================================================

This test suite verifies the `BeforeAfterComparison` class to ensure it correctly 
calculates and summarizes improvements in RAG quality metrics (faithfulness, 
hallucination reduction) when comparing guarded vs unguarded pipelines.
"""
import pytest
from src.evaluator import BeforeAfterComparison

def test_before_after_comparison_metrics():
    comparison = BeforeAfterComparison()
    queries = ["Should I lock in at 5.2%?", "Should I refinance now?"]
    
    results = comparison.run_comparison(None, queries)
    assert "before_guardrails" in results
    assert "after_guardrails" in results
    assert "comparison_summary" in results
    
    summary = results["comparison_summary"]
    assert summary["faithfulness_improvement"] > 0
    assert summary["hallucination_reduction"] > 0
    assert summary["pass_rate_after"] == "100%"
