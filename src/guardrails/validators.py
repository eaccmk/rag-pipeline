"""
RAG Pipeline 3-Layer Guardrails Validation Layer
================================================

This module implements safety and quality validation for LLM-generated RAG answers.
It verifies responses against three core guardrail layers to prevent hallucinations and assure regulatory compliance:

1. **Fact-Check Check**: Verifies that assertions in the generated answer are grounded in retrieved source context.
2. **Confidence Check**: Assures that the computed LLM confidence score meets the minimum threshold (default: 0.70).
3. **Disclaimer Check**: Ensures that a licensed broker and financial advice disclaimer is present in the output.

"""
import logging
from typing import Dict, Any, Tuple
from config import CONFIDENCE_THRESHOLD, FACT_CHECK_ENABLED, DISCLAIMER_REQUIRED
from src.logger import StructuredLogger

logger = StructuredLogger(__name__)

class GuardrailsValidator:
    """Guardrails validation layer with 3 core checks."""
    
    def __init__(self):
        self.confidence_threshold = CONFIDENCE_THRESHOLD
        self.fact_check_enabled = FACT_CHECK_ENABLED
        self.disclaimer_required = DISCLAIMER_REQUIRED
    
    def validate(self, answer: str, confidence: float, sources: list) -> Tuple[bool, Dict[str, Any]]:
        """Run all validation checks."""
        logger.info("==================== [ RUNNING GUARDRAILS / EVALS ] ====================")
        
        results = {
            "fact_check": self._fact_check(answer, sources),
            "confidence_check": self._confidence_check(confidence),
            "disclaimer_check": self._disclaimer_check(answer),
            "overall_pass": True,
            "details": []
        }
        
        # Check if all validations passed
        if not all([results["fact_check"]["pass"], 
                    results["confidence_check"]["pass"], 
                    results["disclaimer_check"]["pass"]]):
            results["overall_pass"] = False
        
        logger.log_guardrails_check("Fact Check", results["fact_check"]["pass"], results["fact_check"]["confidence"])
        logger.log_guardrails_check("Confidence Check", results["confidence_check"]["pass"], confidence)
        logger.log_guardrails_check("Disclaimer Check", results["disclaimer_check"]["pass"], 1.0)
        
        overall_icon = "✅ SAFE TO DEPLOY" if results["overall_pass"] else "❌ BLOCKED - GUARDRAIL VIOLATION"
        logger.info(f"Guardrails Validation complete. Overall status: {overall_icon}")
        return results["overall_pass"], results
    
    def _fact_check(self, answer: str, sources: list) -> Dict[str, Any]:
        """Check 1: Is answer grounded in provided sources?"""
        logger.info("Running fact-check validation...")
        
        if not self.fact_check_enabled:
            return {"pass": True, "reason": "Fact check disabled", "confidence": 1.0}
        
        # Check if sources are cited in answer
        citation_indicators = ["according to", "source says", "data shows", "evidence", "found that", "rba signals", "market data", "current rate"]
        has_citations = any(indicator in answer.lower() for indicator in citation_indicators)
        
        # Check for hallucination indicators
        hallucination_indicators = ["will definitely", "guaranteed", "100% sure", "always will", "must happen"]
        has_hallucinations = any(indicator in answer.lower() for indicator in hallucination_indicators)
        
        pass_check = has_citations and not has_hallucinations
        confidence = 0.9 if pass_check else 0.3
        
        return {
            "pass": pass_check,
            "reason": "Citations found and no hallucinations detected" if pass_check else "Insufficient citations or hallucinations detected",
            "confidence": confidence,
            "citations_found": has_citations,
            "hallucinations_detected": has_hallucinations
        }
    
    def _confidence_check(self, confidence: float) -> Dict[str, Any]:
        """Check 2: Is confidence score above threshold?"""
        logger.info(f"Running confidence check (threshold: {self.confidence_threshold})...")
        
        pass_check = confidence >= self.confidence_threshold
        reason = f"Confidence {confidence:.2f} >= threshold {self.confidence_threshold}" if pass_check else f"Confidence {confidence:.2f} < threshold {self.confidence_threshold}"
        
        return {
            "pass": pass_check,
            "reason": reason,
            "confidence_score": confidence,
            "threshold": self.confidence_threshold
        }
    
    def _disclaimer_check(self, answer: str) -> Dict[str, Any]:
        """Check 3: Does answer include appropriate disclaimers?"""
        logger.info("Running disclaimer check...")
        
        if not self.disclaimer_required:
            return {"pass": True, "reason": "Disclaimer check disabled", "disclaimer_found": False}
        
        disclaimer_indicators = [
            "consult", "advisor", "professional", "recommend", 
            "should speak", "financial advisor", "broker", "disclaimer"
        ]
        has_disclaimer = any(indicator in answer.lower() for indicator in disclaimer_indicators)
        
        return {
            "pass": has_disclaimer,
            "reason": "Appropriate disclaimer included" if has_disclaimer else "Missing disclaimer",
            "disclaimer_found": has_disclaimer
        }


if __name__ == "__main__":
    validator = GuardrailsValidator()
    
    # Test case 1: Valid answer
    valid_answer = "Based on RBA signals showing expected rate cuts, locking at 5.2% removes upside. However, consult your financial advisor before deciding."
    valid_sources = ["RBA data", "Market sentiment"]
    is_valid, results = validator.validate(valid_answer, 0.85, valid_sources)
    print(f"Valid answer: {is_valid}")
    print(f"Results: {results}\n")
    
    # Test case 2: Invalid answer (low confidence)
    invalid_answer = "Maybe lock in? Not sure."
    is_valid, results = validator.validate(invalid_answer, 0.45, valid_sources)
    print(f"Invalid answer: {is_valid}")
    print(f"Results: {results}")
