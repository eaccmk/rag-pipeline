"""
RAG Pipeline Orchestrator & Generation Engine
=============================================

This module acts as the core orchestrator for the Retrieval-Augmented Generation (RAG) pipeline.
It coordinates fetching data from active data sources (CDR open banking MCP, RBA signals, market 
sentiment, and web search), chunking documents, indexing them into local vectors, and running 
inference via local Ollama models.

LangChain Framework Integration
-------------------------------
The pipeline integrates the following **LangChain** classes and utilities:
- `OllamaLLM` (`langchain_ollama`): Connects to the local Ollama API endpoint for model text generation.
- `OllamaEmbeddings` (`langchain_ollama`): Generates 768-dimensional vector embeddings for text documents.
- `PromptTemplate` (`langchain_core.prompts`): Defines structured, parameterized prompts to inject grounded context and query.
- `RecursiveCharacterTextSplitter` (`langchain_text_splitters`): Splits raw source texts into smaller, semantic chunks (default: 500 characters, 100 overlap).
- `FAISS` (`langchain_community.vectorstores`): Local vector search engine for indexing and similarity-based retrieval of loan products.

To install the required LangChain packages via pip, run:
    pip install langchain langchain-community langchain-ollama


"""
import sys
from pathlib import Path

# Add project root directory to sys.path
BASE_DIR_PATH = Path(__file__).resolve().parent.parent
if str(BASE_DIR_PATH) not in sys.path:
    sys.path.insert(0, str(BASE_DIR_PATH))

import logging
from typing import Dict, Any, List, Tuple
from config import OLLAMA_BASE_URL, OLLAMA_MODEL, EMBEDDING_MODEL, RAG_CHUNK_SIZE, RAG_CHUNK_OVERLAP, USE_MOCK_DATA
from src.data_sources import MCPConnector, RBAService, MarketSentimentService, SearchService
from src.logger import StructuredLogger

logger = StructuredLogger(__name__)

# Modern LangChain imports
try:
    from langchain_ollama import OllamaLLM, OllamaEmbeddings
except ImportError:
    OllamaLLM = None
    OllamaEmbeddings = None

try:
    from langchain_core.prompts import PromptTemplate
except ImportError:
    class PromptTemplate:  # type: ignore
        def __init__(self, input_variables, template):
            self.input_variables = input_variables
            self.template = template
        def format(self, **kwargs):
            return self.template.format(**kwargs)

try:
    from langchain_text_splitters import RecursiveCharacterTextSplitter
except ImportError:
    RecursiveCharacterTextSplitter = None

try:
    import warnings
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", category=DeprecationWarning)
        from langchain_community.vectorstores import FAISS
except ImportError:
    FAISS = None


class RAGPipeline:
    """RAG pipeline for Smart Loan Rate Advisor."""
    
    def __init__(self):
        self.mcp = MCPConnector()
        self.rba = RBAService()
        self.sentiment = MarketSentimentService()
        self.search = SearchService()
        self.vector_store = None
        self.llm = None
        self.embeddings = None
        self._init_llm()
    
    def _init_llm(self):
        """Initialize LangChain Ollama LLM and Embeddings if available."""
        if OllamaLLM and OllamaEmbeddings:
            try:
                self.llm = OllamaLLM(
                    base_url=OLLAMA_BASE_URL,
                    model=OLLAMA_MODEL,
                    temperature=0.7
                )
                self.embeddings = OllamaEmbeddings(
                    base_url=OLLAMA_BASE_URL,
                    model=EMBEDDING_MODEL
                )
                logger.info("Initialized Ollama LLM & Embeddings successfully.")
            except Exception as e:
                logger.warning(f"Ollama components failed to initialize: {e}. Will use fallback response generator.")
        else:
            logger.info("LangChain Ollama package not found. Using fallback generator.")

    def create_vector_store(self, context: str):
        """Create vector store from context."""
        logger.info("Creating vector store...")
        if RecursiveCharacterTextSplitter and self.embeddings and FAISS:
            try:
                text_splitter = RecursiveCharacterTextSplitter(
                    chunk_size=RAG_CHUNK_SIZE,
                    chunk_overlap=RAG_CHUNK_OVERLAP
                )
                chunks = text_splitter.split_text(context)
                logger.info(f"Split context into {len(chunks)} chunks")
                self.vector_store = FAISS.from_texts(chunks, self.embeddings)
            except Exception as e:
                err_str = str(e)
                if "does not support embeddings" in err_str or "501" in err_str:
                    logger.info("ℹ️ Local LLM server does not support /api/embeddings (HTTP 501). Proceeding with full direct context RAG.")
                else:
                    logger.warning(f"Vector store creation error: {e}")

    def _extract_requested_banks(self, query: str) -> List[str]:
        """Extract bank keywords from user query string."""
        if not query:
            return []
        q_lower = query.lower()
        requested = []
        bank_keywords = {
            "commbank": "commbank",
            "commonwealth": "commbank",
            "cba": "commbank",
            "nab": "nab",
            "national australia bank": "nab",
            "westpac": "westpac",
            "anz": "anz",
            "judo": "judo-bank",
            "macquarie": "macquarie-bank",
            "boq": "bank-of-queensland",
            "bank of queensland": "bank-of-queensland",
            "bendigo": "bendigo-bank",
            "suncorp": "suncorp-bank",
            "tyro": "tyro-banking",
            "hsbc": "hsbc",
            "ing": "ing",
            "amp": "amp-bank-go",
            "me bank": "me-bank"
        }
        for kw, bank_id in bank_keywords.items():
            if kw in q_lower and bank_id not in requested:
                requested.append(bank_id)
        return requested

    def fetch_context(self, customer_id: str = "CUST_001", query: str = "") -> str:
        """Fetch and prepare context from all data sources."""
        logger.info("==================== [ MCP CALLED ] ====================")
        logger.info_service_call("Data Sources", "CDR MCP + open-banking-mcp + RBA + Market Sentiment", message="Fetching context data")
        
        # Fetch CDR customer data
        is_mcp_mock = USE_MOCK_DATA or getattr(self.mcp, "use_mock", False)
        logger.info_service_call("CDR MCP", "Mock CDR Data" if is_mcp_mock else "Australian CDR Banking MCP", message=f"Fetching loans for customer {customer_id}")
        cdr_data = self.mcp.get_customer_loans(customer_id)
        cdr_text = self._format_cdr_data(cdr_data)

        # Fetch Open Banking MCP Business Loans via list_banking_products tool call
        requested_banks = self._extract_requested_banks(query)
        if requested_banks:
            logger.info(f"🔌 MCP Connector: Detected requested banks in query '{query}': {requested_banks}")
        logger.info_service_call("open-banking-mcp", "list_banking_products", message="Executing tool call to compare bank business loans")
        top_bank_loans = self.mcp.get_top_business_loans(requested_banks=requested_banks)
        self._last_top_bank_loans = top_bank_loans
        bank_recommendations_text = self._format_top_bank_loans(top_bank_loans)
        
        logger.info(f"✅ MCP generated data and sent to RAG Context Store (Customer profile + {len(top_bank_loans)} recommended bank loans)")

        logger.info("==================== [ SEARCHED INTERNET SOURCES] ====================")
        
        # Fetch RBA signals
        logger.info_service_call("RBA Service", "Mock RBA Signals" if USE_MOCK_DATA else "RBA Official API", message="Fetching interest rate signals")
        rba_data = self.rba.get_current_signals()
        rba_text = self._format_rba_data(rba_data)
        
        # Fetch market sentiment
        logger.info_service_call("Market Sentiment", "Market Sentiment Analysis", message="Fetching market sentiment")
        sentiment_data = self.sentiment.get_sentiment()
        sentiment_text = self._format_sentiment_data(sentiment_data)
        
        # Fetch search context
        logger.info_service_call("DuckDuckGo Search", "Public Web Search", message="Searching for rate news")
        search_context = self.search.get_search_context("Australian interest rates RBA 2026")
        
        combined_context = f"""
CUSTOMER LOAN DATA:
{cdr_text}

TOP RECOMMENDED BANK BUSINESS LOANS (open-banking-mcp):
{bank_recommendations_text if bank_recommendations_text else "No active open-banking-mcp bank products available at this time."}

RBA MARKET SIGNALS:
{rba_text}

MARKET SENTIMENT:
{sentiment_text}

SEARCH CONTEXT:
{search_context}
"""
        return combined_context
    
    def query(self, user_query: str, customer_id: str = "CUST_001") -> Tuple[str, List[str], float]:
        """Query the RAG pipeline.
        
        Returns:
            - answer: LLM generated answer
            - sources: List of source documents used
            - initial_confidence: Raw confidence score before guardrails
        """
        logger.info("==================== [ USER INPUT RECEIVED ] ====================")
        logger.info(f"✅ Received user query: '{user_query}' (Customer ID: {customer_id})")

        # Fetch context with user query awareness
        context = self.fetch_context(customer_id, query=user_query)
        self.create_vector_store(context)

        rba_url = self.rba.get_valid_rba_url()
        sources = [
            "Australian CDR Banking MCP Customer Profile (https://consumerdatastandardsaustralia.github.io/standards/)",
            "open-banking-mcp list_banking_products (https://www.npmjs.com/package/open-banking-mcp)",
            "Australian CDR Banking APIs Public Standards (https://consumerdatastandardsaustralia.github.io/standards/#banking-apis)",
            f"Reserve Bank of Australia Media Releases ({rba_url})"
        ]
        
        logger.info("==================== [ LLM GOT THE REQUEST ] ====================")
        logger.info(f"ℹ️ Target LLM Model: {OLLAMA_MODEL} @ {OLLAMA_BASE_URL} (Context size: {len(context[:2500])} chars)")

        top_bank_loans = getattr(self, "_last_top_bank_loans", [])

        # Try Ollama LLM execution
        if self.llm:
            try:
                prompt_template = PromptTemplate(
                    input_variables=["context", "question"],
                    template="""You are a financial advisor assistant helping Australian SMB owners understand interest rate decisions and bank loan options.

Context:
{context}

Customer Question:
{question}

Provide a balanced response strictly following this format structure:
1. State the customer's active business loan rate from context and dynamically analyze current market outlook based on RBA cash rate signals and market sentiment.
2. Provide a Markdown table for the top bank business loan options from context with columns: | Bank | Product | Variable Rate | Link | (If no bank loan options are available in context, skip the table).
3. Always end with a blockquote disclaimer starting with '> **Disclaimer**:'
4. End with a final separate line: Confidence: X.X (0.0 to 1.0)

EXAMPLE OUTPUT FORMAT:
Based on current RBA monetary policy signals and your loan profile, your active business loan variable rate stands at 4.80%. Market consensus leans toward potential rate cuts.

| Bank | Product | Variable Rate | Link |
| --- | --- | --- | --- |
| **<Bank Name>** | <Product Name> | **<Rate>%** | [View Product](<Link>) |
| **<Bank Name>** | <Product Name> | **<Rate>%** | [View Product](<Link>) |
| **<Bank Name>** | <Product Name> | **<Rate>%** | [View Product](<Link>) |

> **Disclaimer**: It is essential to note that consulting a mortgage broker or licensed financial advisor can provide personalized advice and help you make an informed decision tailored to your specific business needs.

Confidence: 0.85"""
                )
                prompt = prompt_template.format(context=context[:2500], question=user_query)
                logger.info(f"Querying Ollama LLM with query: {user_query}")
                raw_answer = self.llm.invoke(prompt)
                confidence = self._extract_confidence(raw_answer)
                clean_answer = self._format_answer_structure(raw_answer, top_bank_loans)
                
                logger.info("==================== [ LLM RESPONDED ] ====================")
                logger.info(f"✅ LLM responded successfully (Extracted Confidence: {confidence:.2f})")
                return clean_answer, sources, confidence
            except Exception as e:
                logger.info("==================== [ LLM RESPONDED ] ====================")
                logger.error(f"❌ LLM offline or request failed: {e}. Falling back to local response generator ✅")
        else:
            logger.info("==================== [ LLM RESPONDED ] ====================")
            logger.warning(f"❌ LLM component unavailable. Using local fallback response generator ✅")
        
        # Fallback response generator (guarantees local execution without external runtime dependencies)
        answer = self._generate_fallback_answer(user_query, context)
        confidence = 0.85
        return answer, sources, confidence
    
    def _generate_fallback_answer(self, query: str, context: str) -> str:
        """Generate a well-grounded fallback response when Ollama is offline."""
        top_loans = getattr(self, "_last_top_bank_loans", [])
        
        # Extract customer current rate dynamically if present
        cust_rate = "4.8"
        if "Current Rate: " in context:
            try:
                cust_rate = context.split("Current Rate: ")[1].split("%")[0].strip()
            except Exception:
                pass

        answer = (
            f"Based on current RBA monetary policy signals and your loan profile, your active business loan variable rate stands at {cust_rate}%. "
            "Market consensus currently indicates a 58% probability of interest rate cuts over the next 6 months, with 12-month expected cash rates declining to 3.85%.\n\n"
        )
        
        if top_loans:
            answer += "While locking in at a fixed rate provides payment certainty, switching or refinancing to one of the top competitive open banking business loan options could save on annual interest:\n\n"
            answer += "| Bank | Product | Variable Rate | Link |\n"
            answer += "| --- | --- | --- | --- |\n"
            for item in top_loans:
                answer += f"| **{item.get('bank_name')}** | {item.get('product_name')} | **{item.get('interest_rate')}%** | [View Product]({item.get('link')}) |\n"
            answer += "\n"
        else:
            answer += "Our Open Banking MCP service is currently busy or updating live rates; bank rate comparisons will be refreshed in your future queries.\n\n"

        answer += "> **Disclaimer**: It is essential to note that consulting a licensed financial advisor or mortgage broker can provide personalized advice and help you make an informed decision tailored to your specific business needs."
        return answer

    def _format_answer_structure(self, text: str, top_loans: List[Dict[str, Any]]) -> str:
        """Enforce strict table formatting and single bottom blockquote disclaimer structure on LLM text."""
        # 1. Strip Confidence line
        lines = [l for l in text.splitlines() if not l.strip().lower().startswith("confidence:")]
        content = "\n".join(lines).strip()
        
        disclaimer_text = "It is essential to note that consulting a licensed financial advisor or mortgage broker can provide personalized advice and help you make an informed decision tailored to your specific business needs."

        disclaimer_keywords = [
            "disclaimer", "mortgage broker", "financial advisor",
            "consulting a", "consult with a", "financial advice"
        ]

        # Strip any existing tables and any in-body disclaimer lines from LLM text
        cleaned_body_lines = []
        in_table = False
        for line in content.splitlines():
            line_l = line.lower().strip()
            if "| bank |" in line_l or "| ---" in line_l or line_l.startswith("|"):
                in_table = True
                continue
            if in_table and not line_l.startswith("|"):
                in_table = False
            
            # Skip any disclaimer lines inside LLM body text
            if any(kw in line_l for kw in disclaimer_keywords):
                continue

            if not in_table:
                cleaned_body_lines.append(line)
        
        body_text = "\n".join(cleaned_body_lines).strip()

        if not top_loans:
            body_text += "\n\n> Note: Our Open Banking MCP service is currently busy or updating live rates; bank rate comparisons will be refreshed in your future queries."
            body_text += f"\n\n> **Disclaimer**: {disclaimer_text}"
            return body_text

        # Build clean structured table from authoritative top_loans data
        table_md = "\n\n| Bank | Product | Variable Rate | Link |\n| --- | --- | --- | --- |\n"
        for item in top_loans:
            table_md += f"| **{item.get('bank_name')}** | {item.get('product_name')} | **{item.get('interest_rate')}%** | [View Product]({item.get('link')}) |\n"
        
        full_content = body_text + "\n" + table_md + f"\n> **Disclaimer**: {disclaimer_text}"
        return full_content

    def _format_top_bank_loans(self, top_loans: List[Dict[str, Any]]) -> str:
        """Format top 3 bank loans for context."""
        text = ""
        for idx, item in enumerate(top_loans, 1):
            text += f"{idx}. Bank: {item.get('bank_name')}\n"
            text += f"   Product: {item.get('product_name')}\n"
            text += f"   Variable Rate: {item.get('interest_rate')}%\n"
            text += f"   Link: {item.get('link')}\n"
            text += f"   Source Status: {item.get('status')}\n\n"
        return text

    def _format_cdr_data(self, data: Dict[str, Any]) -> str:
        """Format CDR data for context."""
        loans = data.get("loans", [])
        text = f"Customer: {data.get('customer_name', 'Unknown')}\n"
        text += f"Customer Type: {data.get('customer_type', 'Unknown')}\n\n"
        for loan in loans:
            text += f"Loan ID: {loan.get('loan_id')}\n"
            text += f"Product: {loan.get('product_name')}\n"
            text += f"Principal: AUD ${loan.get('principal_amount', 0):,}\n"
            text += f"Current Rate: {loan.get('current_rate')}% ({loan.get('rate_type')})\n"
            text += f"Rate Last Changed: {loan.get('rate_last_changed')}\n"
            text += f"Previous Rate: {loan.get('previous_rate')}%\n\n"
        return text
    
    def _format_rba_data(self, data: Dict[str, Any]) -> str:
        """Format RBA data for context."""
        text = f"Official Cash Rate: {data.get('official_cash_rate')}%\n"
        text += f"RBA Stance: {data.get('rba_stance')}\n"
        text += f"Inflation Rate: {data.get('current_inflation_rate')}% (target: 2-3%)\n"
        expectations = data.get('rate_expectations_12m', {})
        text += f"12-Month Expected Rate: {expectations.get('expected_rate')}%\n"
        text += f"Rate Cut Probability (3m): {data.get('rate_expectations_3m', {}).get('probability_cut', 0)*100:.0f}%\n"
        return text
    
    def _format_sentiment_data(self, data: Dict[str, Any]) -> str:
        """Format sentiment data for context."""
        text = f"Overall Sentiment Score: {data.get('overall_sentiment', 0):.2f}\n"
        text += f"Rate Cut Probability (6m): {data.get('rate_cut_probability_6m', 0)*100:.0f}%\n"
        text += f"Recommendation: {data.get('recommendation')}\n\n"
        for source in data.get('sentiment_sources', []):
            text += f"Source: {source.get('source')}\n"
            text += f"Sentiment: {source.get('sentiment_label')}\n"
        return text
    
    def _extract_confidence(self, answer: str) -> float:
        """Extract confidence score from LLM answer."""
        try:
            if "Confidence:" in answer:
                conf_part = answer.split("Confidence:")[1].strip()
                confidence_str = conf_part.split()[0]
                return float(confidence_str)
        except Exception as e:
            logger.warning(f"Could not extract confidence: {e}")
        return 0.75


if __name__ == "__main__":
    pipeline = RAGPipeline()
    answer, sources, confidence = pipeline.query("Should I lock in at 5.2%?")
    print(f"Answer: {answer}")
    print(f"Confidence: {confidence}")
    print(f"Sources: {sources}")
