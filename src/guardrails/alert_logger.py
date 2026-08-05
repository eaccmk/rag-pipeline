"""
RAG Pipeline Guardrails Decision & Audit Logger
===============================================

This module implements the logging layer for guardrail validation decisions. 
It records all pipeline queries, generated answers, verification status ("PASSED" vs "BLOCKED"), 
confidence scores, and computed Ragas evaluation metrics into a structured JSON log file 
(default: `logs/guardrails_alerts.json`) for auditing and security review.

"""
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any
from config import GUARDRAILS_LOG_FILE

logger = logging.getLogger(__name__)

class AlertLogger:
    """Log guardrail validation decisions to JSON."""
    
    def __init__(self, log_file: Path = GUARDRAILS_LOG_FILE):
        self.log_file = log_file
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
    
    def log_decision(self, 
                    query: str, 
                    answer: str, 
                    validation_results: Dict[str, Any],
                    ragas_metrics: Dict[str, float] = None) -> None:
        """Log a guardrail validation decision."""
        decision = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "query": query,
            "answer": answer,
            "validation": validation_results,
            "ragas_metrics": ragas_metrics or {},
            "status": "PASSED" if validation_results.get("overall_pass") else "BLOCKED"
        }
        
        # Append to JSON log file
        try:
            # Read existing logs
            if self.log_file.exists():
                with open(self.log_file, 'r') as f:
                    try:
                        logs = json.load(f)
                    except json.JSONDecodeError:
                        logs = []
            else:
                logs = []
            
            # Append new decision
            logs.append(decision)
            
            # Write back
            with open(self.log_file, 'w') as f:
                json.dump(logs, f, indent=2)
            
            logger.info(f"Logged decision to {self.log_file}")
        except Exception as e:
            logger.error(f"Error logging decision: {e}")
    
    def get_recent_decisions(self, limit: int = 10) -> list:
        """Get recent guardrail decisions."""
        try:
            if self.log_file.exists():
                with open(self.log_file, 'r') as f:
                    logs = json.load(f)
                    return logs[-limit:]
        except Exception as e:
            logger.error(f"Error reading logs: {e}")
        return []
    
    def get_pass_rate(self) -> float:
        """Get percentage of decisions that passed guardrails."""
        try:
            if self.log_file.exists():
                with open(self.log_file, 'r') as f:
                    logs = json.load(f)
                if not logs:
                    return 0.0
                passed = sum(1 for log in logs if log.get("status") == "PASSED")
                return (passed / len(logs)) * 100
        except Exception as e:
            logger.error(f"Error calculating pass rate: {e}")
        return 0.0


if __name__ == "__main__":
    logger_alert = AlertLogger()
    
    # Test logging
    test_decision = {
        "overall_pass": True,
        "fact_check": {"pass": True},
        "confidence_check": {"pass": True, "confidence_score": 0.85},
        "disclaimer_check": {"pass": True}
    }
    
    logger_alert.log_decision(
        query="Should I lock in at 5.2%?",
        answer="Based on data, locking offers certainty. Consult your broker.",
        validation_results=test_decision,
        ragas_metrics={"faithfulness": 0.89, "context_relevance": 0.85}
    )
    
    print(f"Recent decisions: {logger_alert.get_recent_decisions(1)}")
    print(f"Pass rate: {logger_alert.get_pass_rate()}%")
