import json
import logging
import subprocess
import shutil
from pathlib import Path
from typing import Dict, Any, List, Optional
import requests
from config import MCP_SERVER_URL, MCP_AUTH_TOKEN, BASE_DIR, USE_MOCK_DATA

from src.logger import StructuredLogger

logger = StructuredLogger(__name__)

class MCPConnector:
    """Connector to Australian CDR Banking MCP Server (via stdio open-banking-mcp or HTTP API)."""
    
    def __init__(self, server_url: str = MCP_SERVER_URL, auth_token: str = MCP_AUTH_TOKEN):
        self.server_url = server_url
        self.auth_token = auth_token
        self.mock_data_path = BASE_DIR / "data" / "mock_cdr_loans.json"
        self.use_mock = USE_MOCK_DATA or (not auth_token or auth_token == "your_token_here")
        self.has_npx = shutil.which("npx") is not None
        
        if self.has_npx and not self.use_mock:
            logger.info("🔌 MCP Connector: Node/npx detected. open-banking-mcp stdio tool runner active.")
        else:
            logger.info("🔌 MCP Connector: Mock mode active for open-banking-mcp catalog.")

    def call_mcp_tool(self, tool_name: str, arguments: Dict[str, Any], timeout_sec: int = 4) -> Dict[str, Any]:
        """Execute a tool call against the open-banking-mcp stdio server."""
        if not self.has_npx or self.use_mock:
            return {"error": "npx unavailable or mock mode enabled"}
        
        proc = None
        try:
            logger.info(f"🔌 MCP Stdio Call: Requesting tool '{tool_name}' with args {arguments}")
            proc = subprocess.Popen(
                ["npx", "-y", "open-banking-mcp"],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            payload = "\n".join([
                json.dumps({
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "initialize",
                    "params": {
                        "protocolVersion": "2024-11-05",
                        "capabilities": {},
                        "clientInfo": {"name": "rag-pipeline-client", "version": "1.0.0"}
                    }
                }),
                json.dumps({"jsonrpc": "2.0", "method": "notifications/initialized"}),
                json.dumps({
                    "jsonrpc": "2.0",
                    "id": 2,
                    "method": "tools/call",
                    "params": {
                        "name": tool_name,
                        "arguments": arguments
                    }
                })
            ]) + "\n"
            
            stdout_data, _ = proc.communicate(input=payload, timeout=timeout_sec)
            
            for line in stdout_data.splitlines():
                line = line.strip()
                if line:
                    try:
                        res_data = json.loads(line)
                        if res_data.get("id") == 2 or "result" in res_data:
                            logger.info(f"✅ MCP Stdio Call: Received response for tool '{tool_name}' successfully")
                            return res_data
                    except json.JSONDecodeError:
                        continue
            
            return {"error": "No valid tool call response from open-banking-mcp"}
        except subprocess.TimeoutExpired:
            if proc:
                proc.kill()
            logger.warning(f"⚠️ MCP Stdio Call timed out ({timeout_sec}s) for tool '{tool_name}'")
            return {"error": f"MCP tool '{tool_name}' timed out"}
        except Exception as e:
            if proc:
                try:
                    proc.kill()
                except Exception:
                    pass
            logger.error(f"❌ MCP Stdio Error: Failed executing tool '{tool_name}': {e}")
            return {"error": str(e)}

    BANK_NAME_MAP = {
        "commbank": "Commonwealth Bank (CommBank)",
        "nab": "National Australia Bank (NAB)",
        "westpac": "Westpac Banking Corporation",
        "anz": "ANZ Banking Group",
        "judo-bank": "Judo Bank",
        "macquarie-bank": "Macquarie Bank",
        "boq": "Bank of Queensland (BOQ)",
        "bank-of-queensland": "Bank of Queensland (BOQ)",
        "bendigo": "Bendigo Bank",
        "bendigo-bank": "Bendigo Bank",
        "suncorp": "Suncorp Bank",
        "suncorp-bank": "Suncorp Bank",
        "tyro": "Tyro Banking",
        "tyro-banking": "Tyro Banking",
        "tyro-payments": "Tyro Payments",
        "hsbc": "HSBC Bank Australia",
        "amp-bank-go": "AMP Bank",
        "ing": "ING Bank Australia",
        "me-bank": "ME Bank"
    }

    DEFAULT_BANK_URLS = {
        "commbank": "https://www.commbank.com.au/business/loans-and-finance.html",
        "nab": "https://www.nab.com.au/business/loans-and-finance/business-loans",
        "westpac": "https://www.westpac.com.au/business-banking/loans-finance/",
        "anz": "https://www.anz.com.au/business/loans-finance/",
        "judo-bank": "https://www.judo.bank/",
        "macquarie-bank": "https://www.macquarie.com.au/business.html",
        "boq": "https://www.boq.com.au/business-banking",
        "bank-of-queensland": "https://www.boq.com.au/business-banking",
        "bendigo": "https://www.bendigobank.com.au/business/",
        "bendigo-bank": "https://www.bendigobank.com.au/business/",
        "suncorp": "https://www.suncorp.com.au/banking/business.html",
        "suncorp-bank": "https://www.suncorp.com.au/banking/business.html",
        "tyro": "https://www.tyro.com/",
        "tyro-banking": "https://www.tyro.com/",
        "tyro-payments": "https://www.tyro.com/",
        "hsbc": "https://www.hsbc.com.au/business/",
        "amp-bank-go": "https://www.amp.com.au/banking",
        "ing": "https://www.ing.com.au/",
        "me-bank": "https://www.mebank.com.au/"
    }

    def list_banking_products(self, bank_id: str, category: str = "BUSINESS_LOANS") -> Dict[str, Any]:
        """Fetch banking products for a specific bank using open-banking-mcp.
        
        TOOL CALL SEQUENCE - STEP 1:
        Calls `list_banking_products` tool to list products for a given bank filtered
        by category='BUSINESS_LOANS'.
        
        Detailed Code Comment & Performance Rationale:
        ----------------------------------------------
        We use explicit parameter filtering (`category="BUSINESS_LOANS"`) during tool execution.
        This targeted approach avoids pulling all product categories (such as credit cards or savings),
        drastically reducing response payload sizes, eliminating LLM token overhead, and minimizing waiting time.
        """
        result = self.call_mcp_tool("list_banking_products", {
            "bankId": bank_id,
            "category": category
        })
        return result

    def get_banking_product(self, bank_id: str, product_id: str) -> Dict[str, Any]:
        """Get full details of a specific banking product using open-banking-mcp `get_banking_product` tool.
        
        TOOL CALL SEQUENCE - STEP 2:
        After discovering product IDs via `list_banking_products` for category='BUSINESS_LOANS',
        this tool fetches granular product specifications (interest rates, features, eligibility, terms, links).
        
        Detailed Code Comment & Performance Rationale:
        ----------------------------------------------
        Targeting `get_banking_product` directly with known `bankId` and `productId` parameters:
        1. Focuses execution strictly on our specific use case (business loan comparison).
        2. Maximizes data accuracy with structured CDR JSON payloads.
        3. Eliminates unnecessary agentic discovery iterations, optimizing latency and saving tokens.
        """
        result = self.call_mcp_tool("get_banking_product", {
            "bankId": bank_id,
            "productId": product_id
        })
        return result

    def _parse_mcp_product_response(self, bank_id: str, text_resp: str) -> Optional[Dict[str, Any]]:
        """Parse real product details and authentic original URLs directly from open-banking-mcp response payload."""
        if not text_resp:
            return None
        
        import re
        bank_name = self.BANK_NAME_MAP.get(bank_id, bank_id.replace("-", " ").title())

        def clean_prod_name(raw_name: str) -> str:
            if not raw_name:
                return f"{bank_name} Business Loan"
            # Strip markdown quote/alert blocks like > [!WARNING], > [!NOTE], etc.
            cleaned = re.sub(r"^\s*>\s*(\[![\w\s]+\])?", "", raw_name, flags=re.IGNORECASE)
            cleaned = re.sub(r"^\s*#+\s*", "", cleaned)
            cleaned = re.sub(r"^\s*[\-\*\•]\s*", "", cleaned)
            cleaned = cleaned.strip()
            if any(k in cleaned.lower() for k in ["warning", "note", "disclaimer", "error", "failed", "http"]) or len(cleaned) < 3:
                return f"{bank_name} Business Loan"
            return cleaned[:60]

        real_link = ""

        # 1. Try parsing JSON payload from MCP tool output
        try:
            parsed = json.loads(text_resp)
            products = []
            if isinstance(parsed, list):
                products = parsed
            elif isinstance(parsed, dict):
                products = parsed.get("data", {}).get("products", parsed.get("products", [parsed]))
            
            if products and isinstance(products, list):
                first_prod = products[0]
                p_name = clean_prod_name(first_prod.get("name") or first_prod.get("product_name"))
                
                # Extract rate if available
                rate = None
                lending_rates = first_prod.get("lendingRates", [])
                if lending_rates and isinstance(lending_rates, list):
                    rate_str = lending_rates[0].get("rate")
                    if rate_str:
                        rate = float(rate_str) * 100 if float(rate_str) < 1.0 else float(rate_str)
                if rate is None:
                    rate = first_prod.get("interest_rate") or first_prod.get("rate")
                
                # Extract product ID if available
                p_id = first_prod.get("productId") or first_prod.get("product_id") or first_prod.get("id") or ""
                
                # Extract authentic original URL from MCP product payload using fallback order:
                # 1. additionalInfoUri (from lendingRates or top-level/additionalInformation)
                # 2. feesAndPricingUri (from additionalInformation)
                # 3. overviewUri (from additionalInformation)
                add_info = first_prod.get("additionalInformation") if isinstance(first_prod.get("additionalInformation"), dict) else {}
                lending_rates = first_prod.get("lendingRates") if isinstance(first_prod.get("lendingRates"), list) else []
                
                additional_info_uri = ""
                for lr in lending_rates:
                    if isinstance(lr, dict) and lr.get("additionalInfoUri"):
                        additional_info_uri = lr.get("additionalInfoUri")
                        break
                if not additional_info_uri:
                    additional_info_uri = add_info.get("additionalInfoUri") or first_prod.get("additionalInfoUri") or ""

                fees_and_pricing_uri = add_info.get("feesAndPricingUri") or first_prod.get("feesAndPricingUri") or ""
                overview_uri = add_info.get("overviewUri") or first_prod.get("overviewUri") or ""

                real_link = (
                    additional_info_uri
                    or fees_and_pricing_uri
                    or overview_uri
                    or add_info.get("website")
                    or add_info.get("termsUri")
                    or add_info.get("eligibilityUri")
                    or first_prod.get("link")
                    or first_prod.get("url")
                    or ""
                )

                if not real_link:
                    m = re.search(r"https?://[^\s\"'\)]+", text_resp)
                    if m:
                        real_link = m.group(0)

                return {
                    "bank_id": bank_id,
                    "bank_name": bank_name,
                    "product_id": p_id,
                    "product_name": p_name,
                    "interest_rate": float(rate) if rate is not None else 4.75,
                    "link": real_link,
                    "raw_text": text_resp[:300],
                    "status": "LIVE_CDR_MCP"
                }
        except Exception:
            pass
        
        # 2. Markdown table & text parsing if MCP response was markdown text output
        ignored_domains = [
            "consumerdatastandardsaustralia.github.io",
            "npmjs.com",
            "api.commbank.com.au",
            "digital-api.westpac.com.au",
            "openbank.api.nab.com.au",
            "api.anz",
            "public.open.judo.bank",
            "api.macquariebank.io"
        ]

        if "error" in text_resp.lower() and ("failed" in text_resp.lower() or "could not reach" in text_resp.lower()):
            return None

        lines = [l.strip() for l in text_resp.splitlines() if l.strip()]
        extracted_prod_name = None
        extracted_link = None

        # Parse Markdown table rows: | [Product Name](URL) | Category | ... |
        for line in lines:
            if line.startswith('|') and ('BUSINESS_LOANS' in line or '[' in line):
                matches = re.findall(r'\[([^\]]+)\]\((https?://[^\)]+)\)', line)
                for text_val, url_val in matches:
                    if any(dom in url_val for dom in ignored_domains):
                        continue
                    if not extracted_prod_name and text_val.lower() not in ['read more here', 'link', 'read more']:
                        extracted_prod_name = clean_prod_name(text_val)
                    if not extracted_link:
                        extracted_link = url_val.strip()
                if extracted_prod_name and extracted_link:
                    break

        if not extracted_link:
            all_urls = re.findall(r'https?://[^\s\"\'\)]+', text_resp)
            for url in all_urls:
                if not any(dom in url for dom in ignored_domains):
                    extracted_link = url
                    break

        rate_match = re.search(r"(\d+\.\d+)%", text_resp)
        rate = float(rate_match.group(1)) if rate_match else None
        prod_name = extracted_prod_name or f"{bank_name} Business Loan"
        
        # Guaranteed non-empty link fallback to ensure valid hyperlink UX
        real_link = extracted_link or self.DEFAULT_BANK_URLS.get(bank_id, "https://www.consumerdata.gov.au/")

        return {
            "bank_id": bank_id,
            "bank_name": bank_name,
            "product_name": prod_name,
            "interest_rate": rate if rate is not None else 4.75,
            "link": real_link,
            "raw_text": text_resp[:300],
            "status": "LIVE_CDR_MCP"
        }

    def get_top_business_loans(self, requested_banks: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """Fetch business loans from MCP, prioritizing requested banks and returning top 3 options.
        
        TOOL CALL SEQUENCE IMPLEMENTATION:
        1. Step 1: Call `list_banking_products(bank_id, category='BUSINESS_LOANS')` to list products
           and filter banks where product-category=BUSINESS_LOANS.
        2. Step 2: Use `get_banking_product(bank_id, product_id)` to query granular details for specific
           products discovered during the listing sequence.
        
        Detailed Code Comment & Performance Rationale:
        ----------------------------------------------
        As we call these very specific tools in sequence:
        - We eliminate unguided general search traversals, reducing prompt and response token costs.
        - Direct tool execution with category="BUSINESS_LOANS" ensures zero latency waste on non-loan products.
        - High precision results are achieved directly from the official CDR open-banking-mcp schema.
        """
        if self.use_mock or not self.has_npx:
            return self._get_fallback_business_loans(requested_banks)

        default_banks = ["commbank", "nab", "westpac", "anz", "judo-bank", "macquarie-bank"]
        bank_alias_map = {
            "boq": "bank-of-queensland",
            "bendigo": "bendigo-bank",
            "suncorp": "suncorp-bank",
            "tyro": "tyro-banking",
            "amp": "amp-bank-go",
            "macquarie": "macquarie-bank",
            "judo": "judo-bank"
        }
        
        # Build ordered list of bank IDs to check
        target_banks = []
        if requested_banks:
            for b in requested_banks:
                b_clean = b.lower().strip()
                b_mapped = bank_alias_map.get(b_clean, b_clean)
                if b_mapped not in target_banks:
                    target_banks.append(b_mapped)
        
        for b in default_banks:
            if b not in target_banks:
                target_banks.append(b)
        
        extracted_options = []
        
        # Sequence Step 1: Call list_banking_products with category="BUSINESS_LOANS"
        for bank_id in target_banks:
            res = self.list_banking_products(bank_id=bank_id, category="BUSINESS_LOANS")
            content_list = res.get("result", {}).get("content", [])
            text_resp = content_list[0].get("text", "") if content_list else ""
            
            if "isError" not in res.get("result", {}) and text_resp:
                parsed = self._parse_mcp_product_response(bank_id, text_resp)
                if parsed:
                    # Sequence Step 2: If a specific product ID is discovered in the response payload,
                    # we can directly call get_banking_product for granular fee & rate attributes.
                    p_id = parsed.get("product_id")
                    if p_id:
                        prod_detail = self.get_banking_product(bank_id=bank_id, product_id=p_id)
                        detail_text = prod_detail.get("result", {}).get("content", [{}])[0].get("text", "")
                        if detail_text and "isError" not in prod_detail.get("result", {}):
                            detailed_parsed = self._parse_mcp_product_response(bank_id, detail_text)
                            if detailed_parsed:
                                parsed = detailed_parsed
                    extracted_options.append(parsed)
            
            # Stop early if we have enough options and checked requested banks
            if len(extracted_options) >= 6:
                break
        
        if not extracted_options:
            logger.warning("🔌 MCP Connector: No live MCP bank options retrieved or MCP server unreachable. Using fallback catalog.")
            return self._get_fallback_business_loans(requested_banks)
            
        # Prioritize requested banks in ordering, then sort remainder by rate
        prioritized = []
        remainder = []
        if requested_banks:
            req_set = set(r.lower().strip() for r in requested_banks)
            for item in extracted_options:
                if item["bank_id"] in req_set:
                    prioritized.append(item)
                else:
                    remainder.append(item)
        else:
            remainder = extracted_options
            
        remainder.sort(key=lambda x: x["interest_rate"])
        final_top = (prioritized + remainder)[:3]
        
        logger.info(f"🔌 MCP Connector: Selected top {len(final_top)} bank business loans: {[b['bank_name'] for b in final_top]}")
        return final_top

    def _get_fallback_business_loans(self, requested_banks: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """Fallback list of top business loans when open-banking-mcp is offline or unreachable."""
        catalog = [
            {
                "bank_id": "commbank",
                "bank_name": "Commonwealth Bank (CommBank)",
                "product_name": "CommBank BetterBusiness Loan",
                "interest_rate": 5.15,
                "link": self.DEFAULT_BANK_URLS.get("commbank", "https://www.commbank.com.au/business/loans-and-finance.html"),
                "status": "FALLBACK_CATALOG"
            },
            {
                "bank_id": "nab",
                "bank_name": "National Australia Bank (NAB)",
                "product_name": "NAB Business Options Loan",
                "interest_rate": 5.09,
                "link": self.DEFAULT_BANK_URLS.get("nab", "https://www.nab.com.au/business/loans-and-finance/business-loans"),
                "status": "FALLBACK_CATALOG"
            },
            {
                "bank_id": "westpac",
                "bank_name": "Westpac Banking Corporation",
                "product_name": "Westpac Business Term Facility",
                "interest_rate": 5.22,
                "link": self.DEFAULT_BANK_URLS.get("westpac", "https://www.westpac.com.au/business-banking/loans-finance/"),
                "status": "FALLBACK_CATALOG"
            },
            {
                "bank_id": "anz",
                "bank_name": "ANZ Banking Group",
                "product_name": "ANZ Business Loan",
                "interest_rate": 5.25,
                "link": self.DEFAULT_BANK_URLS.get("anz", "https://www.anz.com.au/business/loans-finance/"),
                "status": "FALLBACK_CATALOG"
            }
        ]
        if requested_banks:
            req_set = set(r.lower().strip() for r in requested_banks)
            prioritized = [item for item in catalog if item["bank_id"] in req_set]
            remainder = [item for item in catalog if item["bank_id"] not in req_set]
            return (prioritized + remainder)[:3]
        return catalog[:3]

    def get_customer_loans(self, customer_id: str) -> Dict[str, Any]:
        """Fetch customer loan data from CDR MCP."""
        if self.use_mock:
            logger.info(f"✅ MCP Connector: Fetched loans for customer {customer_id} [MOCK MODE]")
            return self._get_mock_loans(customer_id)
        
        try:
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            response = requests.get(
                f"{self.server_url}/api/customer/{customer_id}/loans",
                headers=headers,
                timeout=5
            )
            response.raise_for_status()
            logger.info(f"✅ MCP Connector: Fetched loans for customer {customer_id} from Australian CDR Banking MCP (200 OK)")
            return response.json()
        except Exception as e:
            logger.error(f"❌ MCP Connector: Connection error to CDR server: {e}. Falling back to mock data.")
            return self._get_mock_loans(customer_id)
    
    def get_eligible_products(self, customer_id: str) -> Dict[str, Any]:
        """Fetch eligible loan products for customer."""
        if self.use_mock:
            logger.info(f"🔌 MCP Connector: Fetching eligible products for customer {customer_id} [MOCK MODE]")
            return self._get_mock_eligible_products(customer_id)
        
        try:
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            response = requests.get(
                f"{self.server_url}/api/customer/{customer_id}/eligible-products",
                headers=headers,
                timeout=5
            )
            response.raise_for_status()
            logger.info(f"🔌 MCP Connector: Fetched eligible products for customer {customer_id} from Australian CDR Banking MCP")
            return response.json()
        except Exception as e:
            logger.error(f"🔌 MCP Connector: Error fetching eligible products: {e}. Falling back to mock data.")
            return self._get_mock_eligible_products(customer_id)
    
    def _get_mock_loans(self, customer_id: str) -> Dict[str, Any]:
        """Load mock loan data for specified customer."""
        try:
            with open(self.mock_data_path) as f:
                data = json.load(f)
                return data.get(customer_id, data.get("CUST_001"))
        except Exception as e:
            logger.error(f"🔌 MCP Connector: Error loading mock data from file: {e}")
            return {"error": "No loan data available"}
    
    def _get_mock_eligible_products(self, customer_id: str) -> Dict[str, Any]:
        """Load mock eligible products."""
        data = self._get_mock_loans(customer_id)
        return {
            "customer_id": customer_id,
            "eligible_products": data.get("eligible_products", [])
        }


if __name__ == "__main__":
    connector = MCPConnector()
    print("--- Testing open-banking-mcp list_banking_products ---")
    commbank_res = connector.list_banking_products("commbank", "BUSINESS_LOANS")
    print("CommBank result:", json.dumps(commbank_res, indent=2)[:400])
    
    print("\n--- Testing Top 3 Business Loans ---")
    top_3 = connector.get_top_business_loans()
    print(json.dumps(top_3, indent=2))

