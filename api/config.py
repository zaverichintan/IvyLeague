import os
import json
from dotenv import load_dotenv

load_dotenv()

# --- Performance Configuration ---
REQUEST_TIMEOUT = 120  # 2 minutes timeout for requests
AI_AGENT_TIMEOUT = 60  # 1 minute timeout for AI agent calls
DATABASE_TIMEOUT = 30  # 30 seconds timeout for database queries
MAX_QUERY_RESULTS = 1000  # Limit results to prevent memory issues

# Chat persistence configuration
CHAT_DB_NAME = "ivy"  # Database name for chat persistence
CHAT_TABLE_NAME = "chats"  # Table name for chat persistence

# Environment variables
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
DATABASE_URL = os.getenv("DATABASE_URL")
CHAT_DATABASE_URL = os.getenv("CHAT_DATABASE_URL")

# Available columns in the transactions table
TRANSACTION_COLUMNS = {
    "account_id": "string - Unique identifier for the account",
    "affected_service": "string - Service affected by the transaction",
    "alert_description": "string - Description of any alerts",
    "aml_risk_score": "numeric - Anti-money laundering risk score",
    "auto_retry_enabled": "boolean - Whether auto retry is enabled",
    "balance_after": "numeric - Account balance after transaction",
    "balance_before": "numeric - Account balance before transaction",
    "block_hash": "string - Blockchain block hash",
    "block_number": "integer - Blockchain block number",
    "bridge_fee_bps": "numeric - Bridge fee in basis points",
    "bridge_protocol": "string - Bridge protocol used",
    "confirmations": "integer - Number of confirmations",
    "credit_amount": "numeric - Amount credited",
    "crypto_amount": "numeric - Amount in cryptocurrency",
    "crypto_token": "string - Type of cryptocurrency token",
    "debit_amount": "numeric - Amount debited",
    "defi_protocol": "string - DeFi protocol used",
    "dest_chain_id": "integer - Destination chain ID",
    "document_types": "string - Types of documents involved",
    "error_code": "string - Error code if any",
    "error_message": "string - Error message if any",
    "estimated_impact": "string - Estimated impact of the transaction",
    "event_index": "integer - Index of the event",
    "event_type": "string - Type of event (e.g., OfframpInitiated, CryptoLockConfirmed)",
    "exchange_rate": "numeric - Exchange rate used",
    "fiat_amount": "numeric - Amount in fiat currency",
    "fiat_currency": "string - Type of fiat currency (e.g., USD, GBP)",
    "flow_type": "string - Type of flow (e.g., crypto_to_fiat_success)",
    "from_address": "string - Source address",
    "from_network": "string - Source network",
    "gas_cost_native": "numeric - Gas cost in native currency",
    "gas_price_gwei": "numeric - Gas price in Gwei",
    "gas_used": "integer - Amount of gas used",
    "incident_id": "string - Incident identifier",
    "kyc_provider": "string - KYC provider",
    "kyc_session_id": "string - KYC session identifier",
    "kyc_status": "string - KYC status (e.g., verified)",
    "ledger_entry_id": "string - Ledger entry identifier",
    "ledger_entry_type": "string - Type of ledger entry",
    "ledger_reference": "string - Ledger reference",
    "lp_fee_bps": "numeric - Liquidity provider fee in basis points",
    "merkle_root": "string - Merkle root hash",
    "min_received": "numeric - Minimum amount received",
    "mitigation_steps": "string - Steps taken for mitigation",
    "network": "string - Blockchain network",
    "next_retry_in": "string - Next retry time",
    "oncall_team": "string - On-call team responsible",
    "pep_check": "string - Politically exposed person check result",
    "pool_address": "string - Pool address",
    "proof_hash": "string - Proof hash",
    "protocol_network": "string - Protocol network",
    "protocol_tvl": "numeric - Total value locked in protocol",
    "protocol_type": "string - Type of protocol",
    "provider": "string - Service provider",
    "relay_node": "string - Relay node",
    "retry_count": "integer - Number of retries",
    "risk_score": "numeric - Risk score",
    "sanctions_check": "string - Sanctions check result",
    "severity": "string - Severity level",
    "sla_breach": "boolean - Whether SLA was breached",
    "slippage_tolerance": "numeric - Slippage tolerance",
    "source_chain_id": "integer - Source chain ID",
    "timestamp": "timestamp - Time of the transaction",
    "to_address": "string - Destination address",
    "to_network": "string - Destination network",
    "transaction_id": "string - Unique transaction identifier",
    "tx_hash": "string - Transaction hash",
    "tx_status": "string - Transaction status (e.g., confirmed, pending)",
    "user_id": "string - User identifier",
    "user_tier": "string - User tier (e.g., silver, gold)",
    "verification_level": "string - Verification level"
}

# CORS configuration
CORS_ORIGINS = [
    "http://localhost:3000",        # React dev server default
    "http://localhost:3001",        # Alternative React dev port
    "http://127.0.0.1:3000",        # Alternative localhost format
    "http://127.0.0.1:3001",        # Alternative localhost format
    "http://localhost:5173",        # Vite dev server default
    "http://127.0.0.1:5173",        # Vite alternative
    "http://localhost:8080",        # Alternative dev port
    "http://127.0.0.1:8080",        # Alternative dev port
    # Add production domains here when deploying
    # "https://your-production-domain.com",
    # "https://www.your-production-domain.com",
]

CORS_HEADERS = [
    "Accept",
    "Accept-Language",
    "Content-Language",
    "Content-Type",
    "Authorization",
    "X-Requested-With",
    "X-CSRF-Token",
    "X-API-Key",
    "Cache-Control",
]

CORS_EXPOSE_HEADERS = [
    "Content-Length",
    "Content-Type",
    "X-Total-Count",
    "X-Page-Count",
]

def validate_environment():
    """Validate required environment variables."""
    if not OPENAI_API_KEY:
        raise RuntimeError("OPENAI_API_KEY environment variable not set")
    
    if not DATABASE_URL:
        raise RuntimeError("DATABASE_URL environment variable not set")
    
    return True 