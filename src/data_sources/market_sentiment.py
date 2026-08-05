import json
import logging
from pathlib import Path
from typing import Dict, Any
from config import BASE_DIR

logger = logging.getLogger(__name__)

class MarketSentimentService:
    """Financial market sentiment and consensus service."""
    
    def __init__(self):
        self.mock_data_path = BASE_DIR / "data" / "mock_market_sentiment.json"
    
    def get_sentiment(self) -> Dict[str, Any]:
        """Get overall market sentiment about interest rates."""
        try:
            with open(self.mock_data_path) as f:
                data = json.load(f)
                logger.info("Fetched market sentiment from mock data")
                return data
        except Exception as e:
            logger.error(f"Error loading sentiment data: {e}")
            return self._default_sentiment()
    
    def get_sentiment_score(self) -> float:
        """Get overall sentiment score (-1.0 to 1.0)."""
        sentiment = self.get_sentiment()
        return sentiment.get("overall_sentiment", 0.5)
    
    def get_rate_cut_probability(self) -> float:
        """Get probability of rate cuts in next 6 months."""
        sentiment = self.get_sentiment()
        return sentiment.get("rate_cut_probability_6m", 0.5)
    
    def get_topics(self) -> list:
        """Get key market topics/headlines."""
        sentiment = self.get_sentiment()
        sources = sentiment.get("sentiment_sources", [])
        topics = []
        for source in sources:
            topics.extend(source.get("topics", []))
        return topics
    
    def get_recommendation(self) -> str:
        """Get sentiment-based recommendation."""
        sentiment = self.get_sentiment()
        return sentiment.get("recommendation", "Insufficient data for recommendation")
    
    def _default_sentiment(self) -> Dict[str, Any]:
        """Return default sentiment if data unavailable."""
        return {
            "overall_sentiment": 0.5,
            "rate_cut_probability_6m": 0.5,
            "recommendation": "Market signals are neutral. Consult your broker."
        }


if __name__ == "__main__":
    sentiment = MarketSentimentService()
    print(f"Sentiment Score: {sentiment.get_sentiment_score()}")
    print(f"Rate Cut Probability (6m): {sentiment.get_rate_cut_probability()}")
    print(f"Topics: {sentiment.get_topics()}")
    print(f"Recommendation: {sentiment.get_recommendation()}")
