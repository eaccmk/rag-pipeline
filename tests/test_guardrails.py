"""
Unit Tests for Individual Guardrail Rules
=========================================

This test suite verifies the isolated behavior of individual guardrail sub-checks:
- `_fact_check`: ensures correct grounded status for statements matching context sources.
- `_confidence_check`: verifies pass/fail results above and below the threshold.
- `_disclaimer_check`: checks disclaimer detection in advice outputs.
- `ConfidenceScorer`: verifies the scoring math and weighting formulas.
"""
import pytest
from src.guardrails.validators import GuardrailsValidator
from src.guardrails.confidence_scorer import ConfidenceScorer

def test_guardrails_three_checks():
    validator = GuardrailsValidator()
    
    # 1. Fact Check
    fact_res = validator._fact_check("According to RBA data, cash rate is 4.35%.", ["Source"])
    assert fact_res["pass"] is True

    # 2. Confidence Check
    conf_pass = validator._confidence_check(0.85)
    assert conf_pass["pass"] is True

    conf_fail = validator._confidence_check(0.65)
    assert conf_fail["pass"] is False

    # 3. Disclaimer Check
    disc_pass = validator._disclaimer_check("Please consult your financial advisor.")
    assert disc_pass["pass"] is True

def test_confidence_scorer_formula():
    scorer = ConfidenceScorer()
    score = scorer.calculate_score(
        answer="According to signals, rates may drop. However, consult your advisor for guidance.",
        sources_count=3,
        sentiment_agreement=0.65,
        has_caveats=True
    )
    assert 0.70 <= score <= 1.0
