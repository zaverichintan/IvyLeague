from fastapi import APIRouter, Query
from ..models.schemas import ApiResponse, TransactionSummary
from ..database.queries import execute_query
import jsonify
import json
import asyncio
from fastapi import HTTPException
from ..ai.agents import failed_transaction_retry_agent
from ..chat.manager import transaction_details_from_db
from ..config import AI_AGENT_TIMEOUT
from ..models.schemas import FailedTransactionRetryResponse, GrafanaWebhookRequest
from ..chat.manager import insert_transaction_details_to_db
from ..ai.slack_agent import send_alert_to_slack
from ..database.connection import get_chats_db_connection

async def with_timeout(coro, timeout_seconds: float, operation_name: str):
    """Wrapper to add timeout to any async operation."""
    try:
        return await asyncio.wait_for(coro, timeout=timeout_seconds)
    except asyncio.TimeoutError:
        raise HTTPException(
            status_code=408, 
            detail=f"{operation_name} timed out. Please try a simpler query or check your connection."
        )


router = APIRouter()

@router.get("/summary", response_model=ApiResponse)
async def get_transaction_summary():
    """Get overall transaction statistics."""
    try:
        sql_query = """
        WITH latest_events AS (
            SELECT *, 
                   ROW_NUMBER() OVER (PARTITION BY transaction_id ORDER BY timestamp::timestamptz DESC) as rn
            FROM transactions
        ),
        transaction_status AS (
            SELECT 
                transaction_id,
                event_type,
                CASE WHEN event_type = 'SettlementConfirmed' THEN 'SUCCESSFUL' ELSE 'FAILED' END as final_status
            FROM latest_events 
            WHERE rn = 1
        )
        SELECT 
            COUNT(*) as total_transactions,
            SUM(CASE WHEN final_status = 'SUCCESSFUL' THEN 1 ELSE 0 END) as successful_transactions,
            SUM(CASE WHEN final_status = 'FAILED' THEN 1 ELSE 0 END) as failed_transactions,
            ROUND(
                (SUM(CASE WHEN final_status = 'SUCCESSFUL' THEN 1 ELSE 0 END)::float / COUNT(*)) * 100, 2
            ) as success_rate
        FROM transaction_status;
        """
        
        result = await execute_query(sql_query)
        if result:
            data = result[0]
            summary = TransactionSummary(
                total_transactions=data['total_transactions'],
                successful_transactions=data['successful_transactions'],
                failed_transactions=data['failed_transactions'],
                success_rate=data['success_rate']
            )
            
            return ApiResponse(
                success=True,
                message="Transaction summary retrieved",
                data=summary.dict()
            )
        else:
            return ApiResponse(
                success=False,
                message="No transaction data found",
                data=None
            )
            
    except Exception as e:
        return ApiResponse(
            success=False,
            message="Failed to get transaction summary",
            error=str(e)
        )

@router.get("/users/{user_id}/transactions", response_model=ApiResponse)
async def get_user_transactions(user_id: str, limit: int = Query(10, ge=1, le=100)):
    """Get transactions for a specific user."""
    try:
        sql_query = f"""
        WITH latest_events AS (
            SELECT *, 
                   ROW_NUMBER() OVER (PARTITION BY transaction_id ORDER BY timestamp::timestamptz DESC) as rn
            FROM transactions 
            WHERE user_id = '{user_id}'
        )
        SELECT 
            transaction_id,
            event_type,
            tx_status,
            fiat_amount,
            fiat_currency,
            crypto_amount,
            crypto_token,
            timestamp,
            CASE WHEN event_type = 'SettlementConfirmed' THEN 'SUCCESSFUL' ELSE 'FAILED' END as final_status
        FROM latest_events 
        WHERE rn = 1 
        ORDER BY timestamp::timestamptz DESC 
        LIMIT {limit};
        """
        
        data = await execute_query(sql_query)
        
        return ApiResponse(
            success=True,
            message=f"Retrieved {len(data)} transactions for user {user_id}",
            data={
                "user_id": user_id,
                "transactions": data,
                "count": len(data)
            }
        )
        
    except Exception as e:
        return ApiResponse(
            success=False,
            message=f"Failed to get transactions for user {user_id}",
            error=str(e)
        )

@router.get("/alerts", response_model=ApiResponse)
async def get_transaction_events():
    """Get all alerts."""
    try:
        sql_query = f"""SELECT * FROM alerts ORDER BY timestamp::timestamptz desc;"""
        data = await execute_query(sql_query)
        
        return ApiResponse(
            success=True,
            message="Alerts retrieved", 
            data=data
        )
        
    except Exception as e:
        return ApiResponse(
            success=False,
            message="Failed to get alerts",
            error=str(e)
        ) 
    
@router.post("/alerts/{alert_id}", response_model=ApiResponse)
async def update_alert(alert_id: str):
    """Update an alert by ID."""
    try:
        conn = await get_chats_db_connection()

        print(f"Updating alert {alert_id}")
        sql_query = f"UPDATE alerts SET is_seen = true WHERE id ='{alert_id}'"
        await conn.execute(sql_query)
        await conn.close()
        return ApiResponse(success=True, message="Alert updated")
    except Exception as e:
        return ApiResponse(success=False, message="Failed to update alert", error=str(e))


@router.post('/webhook',response_model=ApiResponse)
async def grafana_webhook(request: GrafanaWebhookRequest):
    """
    This endpoint listens for POST requests from Grafana's webhook notifier.
    It expects the transaction_id to be passed in the alert's tags.
    
    Example Grafana tag: transaction_id:txn_a7b3c9d1
    """
    try:
        data = request.model_dump()
        print("\n🔔 Received a webhook from Grafana:")
        print(json.dumps(data, indent=2))

        # Only process alerts that are in the 'alerting' state
        if data.get('state') != 'alerting':
            return jsonify({"status": "ignored", "reason": f"State was '{data.get('state')}'"}), 200

        # Extract the transaction_id from the alert's tags
        transaction_id = None
        
        transaction_id = data.get('message', {})
        
        if not transaction_id:
            print("Error: 'transaction_id' tag not found in Grafana alert.")
            return jsonify({"status": "error", "message": "'transaction_id' tag not found in Grafana alert"}), 400

        print(f"Found transaction_id: {transaction_id}. Starting analysis...")
        transaction_details = await transaction_details_from_db(transaction_id)
        # print("transaction_details",transaction_details)

        # Generate simple response with timeout
        try:
            augmented_query = f"""
                User Query: Summary of the transaction
                Transaction Details: {json.dumps(transaction_details, indent=2)}                """
            
            simple_result = await with_timeout(
                failed_transaction_retry_agent.run(augmented_query),
                AI_AGENT_TIMEOUT,
                "Failed transaction retry agent"    
            )
            simple_response = simple_result.data
        except HTTPException as e:
            if e.status_code == 408:  # Timeout
                simple_response = FailedTransactionRetryResponse(
                    summary="I'm here to help with your payment and transaction questions. Could you please rephrase your question?",
                    key_insights=["Response generation timed out"],
                    recommendation="Please try asking your question again or be more specific."
                )
            else:
                raise

        try:
            print("inserting transaction details into the database")
            await insert_transaction_details_to_db(transaction_id, simple_response.summary)
            print("transaction details inserted into the database")
        except Exception as e:
            print(f"Error inserting transaction details into the database: {e}")
        
        try:
            await send_alert_to_slack(transaction_id, simple_response.summary)
        except Exception as e:
            print(f"Error sending alert to Slack: {e}")
        
        # summary = analyze_and_summarize_failure_webhook(transaction_id)
        # In a real system, you would send this summary to Slack, PagerDuty, etc.
        # For this example, we just print it to the console.
        print("\n--- 📊 Grafana-Triggered Analysis Report 📊 ---")
        # print(summary)
        print("-------------------------------------------------")

        return ApiResponse(
            success=True,
            message="Alert processed and analyzed.",
            data=simple_response.model_dump()
        )

    except Exception as e:
        print(f"An error occurred in the webhook: {e}")
        return jsonify({"status": "error", "message": "Internal server error"}), 500