import json
import logging
from pathlib import Path
from typing import Dict, Any
from config import BASE_DIR

logger = logging.getLogger(__name__)

class RBAService:
    """Reserve Bank of Australia data service.
    
    Phase 1: Uses mock data
    Phase 2: Will integrate with Parse.bot RBA API
    """
    
    def __init__(self):
        self.mock_data_path = BASE_DIR / "data" / "mock_rba_signals.json"
    
    def get_current_signals(self) -> Dict[str, Any]:
        """Get current RBA signals (cash rate, rate expectations, lending rates)."""
        try:
            with open(self.mock_data_path) as f:
                data = json.load(f)
                logger.info("Fetched RBA signals from mock data")
                return data
        except Exception as e:
            logger.error(f"Error loading RBA data: {e}")
            return self._default_signals()
    
    def get_cash_rate(self) -> float:
        """Get current official cash rate."""
        signals = self.get_current_signals()
        return signals.get("official_cash_rate", 4.35)
    
    def get_rate_expectations(self, months_ahead: int = 12) -> Dict[str, Any]:
        """Get market expectations for rate changes."""
        signals = self.get_current_signals()
        if months_ahead == 3:
            return signals.get("rate_expectations_3m", {})
        elif months_ahead == 12:
            return signals.get("rate_expectations_12m", {})
        return {}
    
    def get_lending_rates(self) -> Dict[str, float]:
        """Get current lending rates for various products."""
        signals = self.get_current_signals()
        return signals.get("lending_rates_survey", {})
    
    def get_rba_stance(self) -> str:
        """Get RBA monetary policy stance (hawkish, neutral, dovish)."""
        signals = self.get_current_signals()
        return signals.get("rba_stance", "neutral")
    
    def get_valid_rba_url(self) -> str:
        """Dynamically resolve active RBA Media Releases URL for current year with 404 fallback."""
        import datetime
        import requests
        
        current_year = datetime.datetime.now().year
        primary_url = f"https://www.rba.gov.au/media-releases/{current_year}/"
        
        try:
            res = requests.head(primary_url, timeout=3, allow_redirects=True, headers={'User-Agent': 'Mozilla/5.0'})
            if res.status_code == 200:
                logger.info(f"✅ RBA Media Release URL probe: {primary_url} (HTTP 200 OK)")
                return primary_url
            elif res.status_code in (404, 500):
                logger.warning(f"❌ RBA Media Release URL probe: {primary_url} returned HTTP {res.status_code}. Probing fallback...")
                prev_year_url = f"https://www.rba.gov.au/media-releases/{current_year - 1}/"
                prev_res = requests.head(prev_year_url, timeout=3, allow_redirects=True, headers={'User-Agent': 'Mozilla/5.0'})
                if prev_res.status_code == 200:
                    logger.info(f"✅ RBA Media Release Fallback URL probe: {prev_year_url} (HTTP 200 OK)")
                    return prev_year_url
                else:
                    logger.warning(f"❌ RBA Fallback URL probe: {prev_year_url} returned HTTP {prev_res.status_code}")
        except Exception as e:
            logger.warning(f"❌ RBA URL Probe Error: Failed probing media release URL: {e}")
            
        return "https://www.rba.gov.au/media-releases/"

    def _default_signals(self) -> Dict[str, Any]:
        """Return default signals if data unavailable."""
        return {
            "official_cash_rate": 4.35,
            "rba_stance": "neutral",
            "rate_expectations_12m": {"expected_rate": 4.0, "confidence": 0.6}
        }


if __name__ == "__main__":
    rba = RBAService()
    print(f"Cash Rate: {rba.get_cash_rate()}%")
    print(f"Stance: {rba.get_rba_stance()}")
    print(f"12m Expectations: {rba.get_rate_expectations(12)}")
