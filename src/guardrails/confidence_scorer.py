"""
RAG Pipeline LLM Generation Confidence Scorer
=============================================

This module calculates a normalized confidence score (0.0 to 1.0) for the generated answers.
The score is computed heuristically based on four core factors:

1. **Source Count**: The quantity of verified data sources backing the answer (up to +0.30).
2. **Sentiment Agreement**: Level of alignment across financial sentiment metrics (up to +0.20).
3. **Answer Detail**: Length and detail of response text (up to +0.15).
4. **Caveat Language**: Inclusion of professional caveats ("however", "consult", etc.) (up to +0.15).

"""
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class ConfidenceScorer:
    """Calculate confidence scores for LLM answers."""
    
    def __init__(self):
        self.base_score = 0.5
    
    def calculate_score(self, 
                       answer: str, 
                       sources_count: int, 
                       sentiment_agreement: float = 0.5,
                       has_caveats: bool = True) -> float:
        """Calculate confidence score based on multiple factors.
        
        Args:
            - answer: The generated answer
            - sources_count: Number of sources used
            - sentiment_agreement: How much sentiment sources agree (0-1)
            - has_caveats: Whether answer includes appropriate caveats
        
        Returns:
            - Confidence score (0.0 to 1.0)
        """
        score = self.base_score
        
        # Factor 1: Sources (more sources = higher confidence)
        source_score = min(sources_count / 3, 0.3)  # Max +0.3
        score += source_score
        
        # Factor 2: Sentiment agreement
        sentiment_score = abs(sentiment_agreement - 0.5) * 0.2  # Max +0.2
        score += sentiment_score
        
        # Factor 3: Length and detail
        answer_length = len(answer.split())
        if answer_length > 50:
            score += 0.15  # Max +0.15
        
        # Factor 4: Caveats and disclaimers
        caveat_words = ["however", "but", "consider", "consult", "note that", "important"]
        has_caveats_check = any(word in answer.lower() for word in caveat_words)
        if has_caveats_check:
            score += 0.15  # Max +0.15
        
        # Normalize to 0-1 range
        confidence = min(max(score, 0.0), 1.0)
        logger.info(f"Calculated confidence score: {confidence:.2f}")
        return confidence


if __name__ == "__main__":
    scorer = ConfidenceScorer()
    
    answer = "Based on RBA signals, market sentiment suggests rates may decline. However, consult your broker before making decisions."
    score = scorer.calculate_score(answer, sources_count=3, sentiment_agreement=0.62, has_caveats=True)
    print(f"Confidence Score: {score:.2f}")
