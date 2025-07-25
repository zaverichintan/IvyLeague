from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

# --- Request Models ---

class QueryRequest(BaseModel):
    """Request model for natural language queries."""
    query: str

class ChatQueryRequest(BaseModel):
    """Request model for natural language queries with chat context."""
    query: str
    chat_type: Optional[str] = "existing"  # "new" or "existing"
    chat_id: Optional[str] = None  # Required if chat_type is "existing"

# --- Response Models ---

class SQLGenerationResponse(BaseModel):
    """Model for the SQL generation step."""
    sql_query: str = Field(..., description="The generated PostgreSQL query")
    reasoning: str = Field(..., description="Reasoning behind the query construction")

class DataSummaryResponse(BaseModel):
    """Model for the data summarization step."""
    summary: str = Field(..., description="Comprehensive summary of the data")
    key_insights: List[str] = Field(..., description="Key insights from the data")
    transaction_status: Optional[str] = Field(None, description="Overall transaction status")
    recommendation: Optional[str] = Field(None, description="Recommendations based on analysis")


class ResponseSummaryAgent(BaseModel):
    """Model for the summary of complete response generated by llm with all necessary details"""
    summary: str = Field(..., description="Comprehensive summary of the LLM response")
    metadata: str = Field(..., description="key metadata extracted of the LLM response")

class ApiResponse(BaseModel):
    """Standard API response wrapper."""
    success: bool
    message: str
    data: Optional[Any] = None
    error: Optional[str] = None

class QueryResponse(BaseModel):
    """Complete query response for React frontend."""
    success: bool
    query: str
    sql_query: str
    data: List[Dict[str, Any]]
    summary: str
    insights: List[str]
    recommendation: Optional[str] = None
    response_summary: Optional[str] = None
    execution_time_ms: Optional[float] = None
    record_count: int

class ChatResponse(BaseModel):
    """Response model for chat-enabled queries."""
    success: bool
    chat_id: str
    query: str
    sql_query: str
    data: List[Dict[str, Any]]
    summary: str
    insights: List[str]
    recommendation: Optional[str] = None
    response_summary: Optional[str] = None
    execution_time_ms: Optional[float] = None
    record_count: int

# --- Transaction Models ---

class TransactionSummary(BaseModel):
    """Summary model for transaction statistics."""
    total_transactions: int
    successful_transactions: int
    failed_transactions: int
    success_rate: float
    most_common_failure_step: Optional[str] = None
    average_completion_time_hours: Optional[float] = None

class UserTransactions(BaseModel):
    """Model for user transaction summary."""
    user_id: str
    transaction_count: int
    successful_count: int
    failed_count: int
    success_rate: float
    latest_transaction_date: Optional[str] = None
    total_fiat_amount: Optional[float] = None
    currencies: List[str]

# --- Chat Management Models ---

class ChatInfo(BaseModel):
    """Model for chat information."""
    chat_id: str
    title: str
    created_at: str
    updated_at: str
    message_count: int

class ChatHistory(BaseModel):
    """Model for chat history."""
    chat_id: str
    messages: List[Dict[str, Any]]
    created_at: str
    updated_at: str 


class QueryTypeResponse(BaseModel):
    """Model for the query type response."""
    query_type: str = Field(..., description="The type of query to be executed")

class FailedTransactionRetryResponse(BaseModel):
    """Model for the failed transaction retry response."""
    summary: str = Field(..., description="The summary with all the steps to fix the failed transaction")


class GrafanaWebhookRequest(BaseModel):
    """Model for the grafana webhook request."""
    state: str = Field(..., description="The state of the transaction")
    message: str = Field(..., description="The message of the transaction")