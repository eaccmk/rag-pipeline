import sys
from pathlib import Path

# Add project root directory to sys.path
BASE_DIR_PATH = Path(__file__).resolve().parent.parent
if str(BASE_DIR_PATH) not in sys.path:
    sys.path.insert(0, str(BASE_DIR_PATH))

import json
import logging
import time
from flask import Flask, jsonify, request, send_from_directory

from flask_cors import CORS

import requests
from config import (
    DASHBOARD_PORT, DASHBOARD_HOST, BASE_DIR, LOGS_DIR, GUARDRAILS_LOG_FILE,
    OLLAMA_BASE_URL, OLLAMA_MODEL, USE_MOCK_DATA, LOG_LEVEL, EXECUTION_MODE, DEFAULT_THEME, APP_ENV,
    N8N_WEBHOOK_URL, N8N_BASE_URL, USE_N8N_PIPELINE, QDRANT_HOST, QDRANT_PORT, QDRANT_COLLECTION
)


from src.health_checker import OllamaHealthChecker
from src.rag_pipeline import RAGPipeline
from src.guardrails import GuardrailsValidator, AlertLogger
from src.evaluator import RAGEvaluator, BeforeAfterComparison
from src.data_sources import RBAService, MarketSentimentService, MCPConnector

from src.logger import StructuredLogger

app = Flask(__name__, static_folder=".")
CORS(app)
logger = StructuredLogger(__name__)

health_checker = OllamaHealthChecker(OLLAMA_BASE_URL, OLLAMA_MODEL)
pipeline = RAGPipeline()
validator = GuardrailsValidator()
alert_logger = AlertLogger()
evaluator = RAGEvaluator()
rba_service = RBAService()
sentiment_service = MarketSentimentService()
mcp_connector = MCPConnector()

@app.route("/")
def index():
    return send_from_directory(".", "index.html")

@app.route("/api/health")
@app.route("/api/healthz")
@app.route("/health")
@app.route("/healthz")
def health_status():
    return jsonify(health_checker.check_health())

@app.route("/api/ollama-status")
def ollama_status():
    """Get Ollama availability status."""
    health_checker.check_connection()
    if APP_ENV == "production" and not health_checker.is_available:
        return jsonify({
            "available": False,
            "error": "Ollama service unavailable",
            "message": "Service temporarily unavailable. Please try again later."
        }), 503
    
    return jsonify({
        "available": health_checker.is_available,
        "model": OLLAMA_MODEL,
        "base_url": OLLAMA_BASE_URL,
        "mock_mode": not health_checker.is_available and APP_ENV != "production"
    })

@app.route("/api/config", methods=["GET", "POST"])
def get_config():
    global USE_N8N_PIPELINE
    if request.method == "POST":
        data = request.json or {}
        if "use_n8n_pipeline" in data:
            USE_N8N_PIPELINE = bool(data["use_n8n_pipeline"])
            logger.info(f"🔄 Updated USE_N8N_PIPELINE state to: {USE_N8N_PIPELINE}")

    health_checker.check_connection()
    is_mock_active = USE_MOCK_DATA or getattr(mcp_connector, "use_mock", False) or not health_checker.is_available
    return jsonify({
        "ollama_model": OLLAMA_MODEL,
        "ollama_base_url": OLLAMA_BASE_URL,
        "use_mock_data": is_mock_active,
        "log_level": LOG_LEVEL,
        "execution_mode": EXECUTION_MODE,
        "default_theme": DEFAULT_THEME,
        "use_n8n_pipeline": USE_N8N_PIPELINE,
        "n8n_webhook_url": N8N_WEBHOOK_URL,
        "qdrant_host": QDRANT_HOST,
        "qdrant_port": QDRANT_PORT
    })


@app.route("/api/available-models")
def available_models():
    try:
        response = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=3)
        if response.status_code == 200:
            models = response.json().get("models", [])
            return jsonify({
                "available": True,
                "models": [m.get("name") for m in models]
            })
    except Exception as e:
        return jsonify({
            "available": False,
            "error": str(e),
            "models": []
        }), 500

@app.route("/api/analyze", methods=["POST"])
@app.route("/api/query", methods=["POST"])
def process_query():
    data = request.json or {}
    user_query = data.get("query", "Should I lock in at 5.2% given current market conditions?")
    customer_id = data.get("customer_id", "CUST_001")
    use_n8n = data.get("use_n8n", USE_N8N_PIPELINE)

    # Check if user requested or configured n8n execution
    if use_n8n:
        webhook_urls = [
            N8N_WEBHOOK_URL,
            N8N_WEBHOOK_URL.replace('/webhook/', '/webhook-test/')
        ]
        for w_url in webhook_urls:
            try:
                logger.info(f"🔗 Forwarding query to n8n Webhook: {w_url}")
                resp = requests.post(
                    w_url,
                    json={"query": user_query, "customer_id": customer_id},
                    timeout=8
                )
                if resp.status_code == 200:
                    n8n_payload = resp.json()
                    logger.info(f"✅ Successfully received response from n8n Workflow via {w_url}!")
                    return jsonify(n8n_payload)
                else:
                    logger.warning(f"⚠️ n8n Webhook ({w_url}) returned status {resp.status_code}.")
            except Exception as e:
                logger.warning(f"⚠️ Failed to communicate with n8n webhook ({w_url}): {e}.")

        
        logger.warning("⚠️ All n8n Webhook attempts failed. Falling back to Python native pipeline.")

    
    # Fallback to Python Native RAG execution
    answer, sources, confidence = pipeline.query(user_query, customer_id)
    is_valid, validation_results = validator.validate(answer, confidence, sources)
    ground_truth_context = "Interest rate advisor grounding context."
    ragas_metrics = evaluator.evaluate_answer(user_query, answer, sources, ground_truth_context)
    
    # Log alert
    alert_logger.log_decision(user_query, answer, validation_results, ragas_metrics)
    
    logger.info("==================== [ DATA SENT TO USER ] ====================")
    logger.info("✅ Response, guardrails validation, and RAGAS metrics payload delivered to user interface.")
    
    health_checker.check_connection()
    is_mock_active = USE_MOCK_DATA or getattr(mcp_connector, "use_mock", False) or not health_checker.is_available

    return jsonify({
        "query": user_query,
        "answer": answer,
        "confidence": confidence,
        "sources": sources,
        "is_valid": is_valid,
        "validation_results": validation_results,
        "validation": validation_results,
        "ragas_metrics": ragas_metrics,
        "is_mock": is_mock_active,
        "executor": "python_native_rag"
    })


@app.route("/api/alerts", methods=["GET", "POST"])
def handle_alerts():
    if request.method == "POST":
        data = request.json or {}
        user_query = data.get("query", "n8n Executed Query")
        answer = data.get("answer", "")
        validation = data.get("validation", data.get("validation_results", {}))
        ragas_metrics = data.get("ragas_metrics", {})
        alert_logger.log_decision(user_query, answer, validation, ragas_metrics)
        logger.info("📜 n8n Post-Response Audit Log Decision recorded into database!")
        return jsonify({"status": "logged", "timestamp": time.time()})

    decisions = alert_logger.get_recent_decisions(20)
    return jsonify({
        "alerts": decisions,
        "pass_rate": alert_logger.get_pass_rate()
    })


@app.route("/api/stats", methods=["GET"])
def get_stats():
    decisions = alert_logger.get_recent_decisions(100)
    total = len(decisions)
    passed = sum(1 for d in decisions if d.get("status") == "PASSED")
    avg_conf = sum(d.get("validation", {}).get("confidence_check", {}).get("confidence_score", 0.8) for d in decisions) / total if total > 0 else 0.85
    
    return jsonify({
        "total_queries": total or 1,
        "pass_rate": round((passed / total * 100) if total > 0 else 100.0, 1),
        "average_confidence": round(avg_conf, 2),
        "rba_cash_rate": rba_service.get_cash_rate(),
        "market_sentiment": sentiment_service.get_sentiment_score()
    })

@app.route("/api/market_data", methods=["GET"])
def get_market_data():
    return jsonify({
        "rba": rba_service.get_current_signals(),
        "sentiment": sentiment_service.get_sentiment(),
        "customer": mcp_connector.get_customer_loans("CUST_001"),
        "top_business_loans": mcp_connector.get_top_business_loans()
    })

@app.route("/api/mcp/business-loans", methods=["GET"])
def get_mcp_business_loans():
    """Endpoint exposing open-banking-mcp list_banking_products results for top bank business loans."""
    loans = mcp_connector.get_top_business_loans()
    return jsonify({
        "mcp_server": "open-banking-mcp",
        "tool_called": "list_banking_products",
        "category": "BUSINESS_LOANS",
        "top_recommendations": loans
    })

@app.route("/api/comparison", methods=["GET"])
def get_comparison():
    comparison = BeforeAfterComparison()
    test_queries = [
        "Should I lock in at 5.2% given current market conditions?",
        "Is now a good time to refinance my variable rate loan?",
        "How will the RBA interest rate decision affect my loan?"
    ]
    return jsonify(comparison.run_comparison(pipeline, test_queries))

@app.route("/api/eval", methods=["GET", "POST"])
@app.route("/api/eval/", methods=["GET", "POST"])
@app.route("/api/eval-suite", methods=["GET", "POST"])
@app.route("/api/eval-suite/", methods=["GET", "POST"])
@app.route("/api/evaluate", methods=["GET", "POST"])
@app.route("/api/evaluate/", methods=["GET", "POST"])
def run_evaluation_suite():
    """Execute automated evaluation suite across golden test queries.
    
    Can be invoked via GET or POST:
    - POST payload accepts optional `test_queries` (list), `customer_id` (str),
      and `trigger_source` (e.g. 'n8n_workflow_1.1').
    - Returns aggregate Ragas scores (context_relevance, faithfulness, answer_relevance)
      and individual query evaluation results.
    - Also records decisions into AlertLogger for the dashboard audit trail.
    """
    data = {}
    if request.method == "POST":
        data = request.json or {}
        
    test_queries = data.get("test_queries") or data.get("queries")
    customer_id = data.get("customer_id", "CUST_001")
    trigger_source = data.get("trigger_source", "manual")
    
    logger.info(f"📊 Starting Evaluation Suite run (trigger: {trigger_source}, queries: {len(test_queries) if test_queries else 'default golden'})")
    
    suite_results = evaluator.evaluate_suite(
        pipeline=pipeline,
        queries=test_queries,
        customer_id=customer_id,
        validator=validator
    )
    
    # Log each evaluated query into alert logger
    for item in suite_results.get("queries_evaluated", []):
        alert_logger.log_decision(
            query=f"[{trigger_source}] {item['query']}",
            answer=item.get("answer_snippet", ""),
            validation_results=item.get("validation_results", item.get("validation_checks", {})),
            ragas_metrics=item.get("ragas_metrics", {})
        )
        
    suite_results["trigger_source"] = trigger_source
    suite_results["collection_tested"] = data.get("collection", QDRANT_COLLECTION)
    
    logger.info(f"✅ Evaluation Suite finished: status={suite_results['status']}, pass_rate={suite_results['pass_rate']}, overall_score={suite_results['aggregate_metrics']['overall_ragas_score']}")
    
    return jsonify(suite_results)

@app.route("/<path:path>")
def static_files(path):
    if path.startswith("api/"):
        return jsonify({"error": f"API endpoint /{path} not found"}), 404
    return send_from_directory(".", path)

if __name__ == "__main__":
    print(f"Starting Smart Loan Rate Advisor Web Dashboard at http://{DASHBOARD_HOST}:{DASHBOARD_PORT}")
    app.run(host=DASHBOARD_HOST, port=DASHBOARD_PORT, debug=True)
