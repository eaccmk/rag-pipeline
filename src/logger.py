import logging
import sys
from typing import Optional, Dict, Any
from config import LOG_LEVEL, LOG_FORMAT, USE_MOCK_DATA, EXECUTION_MODE

class ColoredFormatter(logging.Formatter):
    """Custom logging formatter that colorizes log level tags and step headers using ANSI escape codes."""

    RESET = "\033[0m"
    BOLD = "\033[1m"
    BLUE = "\033[1;34m"

    LEVEL_COLORS = {
        logging.DEBUG: "\033[36m",      # Cyan
        logging.INFO: "\033[32m",       # Green
        logging.WARNING: "\033[33m",    # Orange / Yellow
        logging.ERROR: "\033[31m",      # Red
        logging.CRITICAL: "\033[1;31m"  # Bold Red
    }

    def format(self, record):
        color = self.LEVEL_COLORS.get(record.levelno, self.RESET)
        orig_levelname = record.levelname
        record.levelname = f"{color}{self.BOLD}{record.levelname}{self.RESET}"
        
        orig_msg = record.msg
        if isinstance(record.msg, str) and "====================" in record.msg:
            record.msg = f"{self.BLUE}{record.msg}{self.RESET}"
            
        formatted_message = super().format(record)
        record.msg = orig_msg
        record.levelname = orig_levelname
        return formatted_message

class StructuredLogger:
    """Custom logger with structured logging capabilities."""
    
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(getattr(logging, LOG_LEVEL.upper(), logging.INFO))
        self.logger.propagate = False
        
        if not self.logger.handlers:
            handler = logging.StreamHandler(sys.stdout)
            formatter = ColoredFormatter(LOG_FORMAT)
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
        else:
            for h in self.logger.handlers:
                h.setFormatter(ColoredFormatter(LOG_FORMAT))
    
    def info(self, msg: str):
        if "mcp" in msg.lower() and not msg.startswith("🔌") and "=" not in msg and "-" not in msg:
            msg = f"🔌 {msg}"
        self.logger.info(msg)
        
    def debug(self, msg: str):
        if "mcp" in msg.lower() and not msg.startswith("🔌") and "=" not in msg and "-" not in msg:
            msg = f"🔌 {msg}"
        self.logger.debug(msg)
        
    def warning(self, msg: str):
        if "mcp" in msg.lower() and not msg.startswith("🔌") and "=" not in msg and "-" not in msg:
            msg = f"🔌 {msg}"
        self.logger.warning(msg)
        
    def error(self, msg: str):
        if "mcp" in msg.lower() and not msg.startswith("🔌") and "=" not in msg and "-" not in msg:
            msg = f"🔌 {msg}"
        self.logger.error(msg)

    def info_service_call(self, service_name: str, data_source: str, status: str = 'ok', message: str = '', level: str = 'info'):
        is_mcp = "mcp" in service_name.lower() or "mcp" in data_source.lower()
        prefix = "🔌 " if is_mcp else ""
        msg = f"{prefix}{service_name}: {message} | Source: {data_source} | Status: {status.upper()}"
        if USE_MOCK_DATA or 'mock' in data_source.lower():
            msg += " [MOCK MODE]"
        
        log_func = getattr(self.logger, level.lower(), self.logger.info)
        log_func(msg)

    def debug_detailed(self, message: str, context: Optional[Dict[str, Any]] = None):
        msg = message
        if context:
            msg += f" | Context: {context}"
        self.logger.debug(msg)

    def log_rag_execution(self, query: str, step: int, details: str):
        self.logger.info(f"RAG Pipeline - Step {step}: {details} | Query: {query}")

    def log_guardrails_check(self, check_name: str, result: bool, confidence: float):
        status = "✅ PASS" if result else "❌ FAIL"
        self.logger.info(f"Guardrails [{check_name}]: {status} (confidence: {confidence:.2f})")
