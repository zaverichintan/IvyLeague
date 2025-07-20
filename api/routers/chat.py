import json
from datetime import datetime
from fastapi import APIRouter, HTTPException, Query
from ..models.schemas import (
    QueryRequest, ChatQueryRequest, ChatResponse, QueryResponse, 
    ApiResponse, ChatInfo, ChatHistory, SQLGenerationResponse, DataSummaryResponse
)
from ..ai.agents import sql_agent, summary_agent, response_summary_agent, query_type_agent
from ..database.queries import execute_query, validate_and_fix_query, with_timeout
from ..chat.manager import (
    create_new_chat, update_chat_history, load_chat_messages_from_db,
    get_all_chats_from_db, load_chat_history_from_db, delete_chat_from_db,
    chat_exists_in_db, delete_chat_from_memory, save_chat_query
)
from ..config import TRANSACTION_COLUMNS, AI_AGENT_TIMEOUT

router = APIRouter()

async def handle_simple_llm_query(request: ChatQueryRequest, chat_id: str, message_history: list, start_time: datetime) -> ChatResponse:
    """Handle simple queries that don't require SQL execution."""
    try:
        # Use summary agent for simple conversational responses
        simple_context = f"""
        User Query: {request.query}
        
        This is a simple conversational query that doesn't require database analysis.
        Provide a helpful, informative response based on general knowledge about 
        financial transactions, payment processing, or answer the user's question directly.
        """
        
        # Generate simple response with timeout
        try:
            simple_result = await with_timeout(
                summary_agent.run(simple_context, message_history=message_history if message_history else []),
                AI_AGENT_TIMEOUT,
                "Simple query response generation"
            )
            simple_response = simple_result.data
        except HTTPException as e:
            if e.status_code == 408:  # Timeout
                simple_response = DataSummaryResponse(
                    summary="I'm here to help with your payment and transaction questions. Could you please rephrase your question?",
                    key_insights=["Response generation timed out"],
                    recommendation="Please try asking your question again or be more specific."
                )
            else:
                raise
        
        # Calculate execution time
        execution_time = (datetime.now() - start_time).total_seconds() * 1000
        
        # Create the response object for simple queries
        chat_response = ChatResponse(
            success=True,
            chat_id=chat_id,
            query=request.query,
            sql_query="",  # No SQL for simple queries
            data=[],  # No data for simple queries
            summary=simple_response.summary,
            insights=simple_response.key_insights,
            recommendation=simple_response.recommendation,
            response_summary=None,  # Will be filled after summary generation
            execution_time_ms=execution_time,
            record_count=0
        )
        
        # Generate response summary using response_summary_agent
        response_summary = None
        try:
            response_context = f"""
            User Query: {request.query}
            Query Type: Simple conversational query (no SQL needed)
            Response Summary: {simple_response.summary}
            Key Insights: {', '.join(simple_response.key_insights)}
            Recommendation: {simple_response.recommendation or 'None'}
            Execution Time: {execution_time:.0f}ms
            Success: {chat_response.success}
            """
            
            summary_agent_result = await with_timeout(
                response_summary_agent.run(response_context),
                AI_AGENT_TIMEOUT,
                "Response summary generation"
            )
            response_summary = summary_agent_result.data.summary + " " + str(summary_agent_result.data.metadata)    
        except HTTPException as e:
            if e.status_code == 408:  # Timeout
                response_summary = f"Summary: {simple_response.summary[:100]}... (Summary generation timed out)"
            else:
                response_summary = f"Summary generation failed: {str(e)}"
        except Exception as e:
            response_summary = f"Summary generation error: {str(e)}"
        
        # Update the chat response with the generated summary
        chat_response.response_summary = response_summary
        
        # Update chat history with timeout protection
        try:
            all_messages = simple_result.all_messages() if 'simple_result' in locals() else []
            await update_chat_history(chat_id, all_messages, request.query, chat_response.dict(), response_summary)
        except Exception:
            # Don't fail the request if chat history update fails
            pass
        
        return chat_response
        
    except HTTPException:
        raise
    except Exception as e:
        execution_time = (datetime.now() - start_time).total_seconds() * 1000
        
        return ChatResponse(
            success=False,
            chat_id=chat_id,
            query=request.query,
            sql_query="",
            data=[],
            summary=f"Error handling simple query: {str(e)}",
            insights=[],
            recommendation=None,
            response_summary=None,
            execution_time_ms=execution_time,
            record_count=0
        )

@router.post("/query", response_model=ChatResponse)
async def handle_chat_query(request: ChatQueryRequest):
    """
    Main endpoint for natural language queries with conversation context.
    Processes queries through the complete AI workflow with chat history.
    """
    start_time = datetime.now()
    
    try:
        # Handle chat context
        if request.chat_type == "new":
            chat_id = create_new_chat()
            message_history = []
        else:
            if not request.chat_id:
                raise HTTPException(status_code=400, detail="chat_id is required when chat_type is 'existing'")
            
            chat_id = request.chat_id
            
            # Check if chat exists in database or memory cache
            from ..chat.manager import chat_message_cache
            chat_exists = await chat_exists_in_db(chat_id) or chat_id in chat_message_cache
            if not chat_exists:
                raise HTTPException(status_code=404, detail=f"Chat {chat_id} not found")
            
            # Load messages from database/cache for existing chat
            message_history = await load_chat_messages_from_db(chat_id)
        
        # Step 1: Classify query type (simple vs SQL)
        try:
            query_type_result = await with_timeout(
                query_type_agent.run(request.query, message_history=message_history if message_history else []),
                AI_AGENT_TIMEOUT,
                "Query type classification"
            )
            query_type = query_type_result.data.query_type
        except HTTPException as e:
            if e.status_code == 408:  # Timeout
                # Default to SQL if classification fails
                query_type = "sql"
            else:
                raise
        except Exception:
            # Default to SQL if classification fails
            query_type = "sql"
        
        # Handle simple queries without SQL
        if query_type == "simple":
            return await handle_simple_llm_query(request, chat_id, message_history, start_time)
        
        # Step 2: Augment query with dataset context for SQL queries
        augmented_query = f"""
        User Query: {request.query}
        Available Dataset Columns: {json.dumps(TRANSACTION_COLUMNS, indent=2)}
        Please generate a PostgreSQL query to answer this question.
        """
        print(message_history)
        # Step 3: Generate SQL query with timeout
        try:
            if message_history:
                sql_result = await with_timeout(
                    sql_agent.run(augmented_query, message_history=message_history),
                    AI_AGENT_TIMEOUT,
                    "SQL generation"
                )
            else:
                sql_result = await with_timeout(
                    sql_agent.run(augmented_query),
                    AI_AGENT_TIMEOUT,
                    "SQL generation"
                )
        except HTTPException as e:
            if e.status_code == 408:  # Timeout
                raise HTTPException(
                    status_code=408,
                    detail="AI query generation timed out. Please try a simpler question."
                )
            raise
        
        sql_response: SQLGenerationResponse = sql_result.data
        
        # Step 4: Execute SQL query with timeout
        
        # Validate and fix common query issues
        validated_query = validate_and_fix_query(sql_response.sql_query)
        if validated_query != sql_response.sql_query:
            sql_response.sql_query = validated_query
        
        try:
            data = await execute_query(sql_response.sql_query)
        except HTTPException as e:
            if e.status_code == 400 and "computed column" in e.detail:
                # Retry with a fresh SQL generation without conversation history
                fresh_sql_result = await with_timeout(
                    sql_agent.run(augmented_query),  # No message history
                    AI_AGENT_TIMEOUT,
                    "Fresh SQL generation"
                )
                fresh_sql_response: SQLGenerationResponse = fresh_sql_result.data
                fresh_validated_query = validate_and_fix_query(fresh_sql_response.sql_query)
                
                # Try executing the fresh query
                data = await execute_query(fresh_validated_query)
                sql_response.sql_query = fresh_validated_query
            else:
                raise
        
        # Step 5: Generate AI summary with timeout (only if we have data or for context)
        try:
            if data:
                # Limit data sent to summary agent to prevent token overflow
                summary_data = data[:50] if len(data) > 50 else data
                data_context = f"""
                Original Query: {request.query}
                Retrieved Data ({len(data)} rows, showing first {len(summary_data)}):
                {json.dumps(summary_data, indent=2, default=str)}
                {"... (additional rows truncated for analysis)" if len(data) > 50 else ""}
                Total rows: {len(data)}
                """
                
                # Use SQL result's message history for summary agent
                summary_result = await with_timeout(
                    summary_agent.run(data_context, message_history=sql_result.all_messages()),
                    AI_AGENT_TIMEOUT,
                    "AI summary generation"
                )
                summary_response: DataSummaryResponse = summary_result.data
            else:
                summary_response = DataSummaryResponse(
                    summary="No data found matching the query criteria.",
                    key_insights=["No transactions found for the specified criteria"],
                    recommendation="Try adjusting search parameters or check transaction IDs"
                )
                
                # Create summary result with empty data context
                summary_result = await with_timeout(
                    summary_agent.run("No data found for the query.", message_history=sql_result.all_messages()),
                    AI_AGENT_TIMEOUT,
                    "AI summary generation"
                )
        except HTTPException as e:
            if e.status_code == 408:  # Timeout
                # If summary times out, provide basic response
                summary_response = DataSummaryResponse(
                    summary=f"Query executed successfully. Retrieved {len(data)} records.",
                    key_insights=[f"Found {len(data)} matching records"],
                    recommendation="Data retrieved successfully. Summary generation timed out."
                )
                summary_result = sql_result  # Use SQL result as fallback
            else:
                raise
        
        # Calculate execution time
        execution_time = (datetime.now() - start_time).total_seconds() * 1000
        
        # Create the response object
        chat_response = ChatResponse(
            success=True,
            chat_id=chat_id,
            query=request.query,
            sql_query=sql_response.sql_query,
            data=data,
            summary=summary_response.summary,
            insights=summary_response.key_insights,
            recommendation=summary_response.recommendation,
            response_summary=None,  # Will be filled after summary generation
            execution_time_ms=execution_time,
            record_count=len(data)
        )

        # Step 6: Generate response summary using response_summary_agent
        response_summary = None
        try:
            # Create comprehensive response context for summarization
            response_context = f"""
            User Query: {request.query}
            SQL Query: {sql_response.sql_query}
            Data Summary: {summary_response.summary}
            Key Insights: {', '.join(summary_response.key_insights)}
            Recommendation: {summary_response.recommendation or 'None'}
            Records Found: {len(data)}
            Execution Time: {execution_time:.0f}ms
            Success: {chat_response.success}
            """
            
            summary_agent_result = await with_timeout(
                response_summary_agent.run(response_context),
                AI_AGENT_TIMEOUT,
                "Response summary generation"
            )
            print(summary_agent_result.data)
            response_summary = summary_agent_result.data.summary + " " + str(summary_agent_result.data.metadata)    
        except HTTPException as e:
            if e.status_code == 408:  # Timeout
                response_summary = f"Summary: {summary_response.summary[:100]}... (Summary generation timed out)"
            else:
                response_summary = f"Summary generation failed: {str(e)}"
        except Exception as e:
                         response_summary = f"Summary generation error: {str(e)}"
        
        # Update the chat response with the generated summary
        chat_response.response_summary = response_summary
        
        # Step 7: Update chat history with timeout protection
        try:
            all_messages = summary_result.all_messages() if 'summary_result' in locals() else sql_result.all_messages()
            await update_chat_history(chat_id, all_messages, request.query, chat_response.dict(), response_summary)
        except Exception:
            # Don't fail the request if chat history update fails
            pass
        
        return chat_response
        
    except HTTPException:
        raise
    except Exception as e:
        execution_time = (datetime.now() - start_time).total_seconds() * 1000
        
        return ChatResponse(
            success=False,
            chat_id=request.chat_id or "unknown",
            query=request.query,
            sql_query="",
            data=[],
            summary=f"Error: {str(e)}",
            insights=[],
            recommendation=None,
            response_summary=None,
            execution_time_ms=execution_time,
            record_count=0
        )

@router.post("/query-simple", response_model=QueryResponse)
async def handle_simple_query(request: QueryRequest):
    """
    Backward compatibility endpoint for simple queries without chat context.
    Creates a new chat for each query (no conversation memory).
    """
    # Convert to chat request and create new chat
    chat_request = ChatQueryRequest(
        query=request.query,
        chat_type="new",
        chat_id=None
    )
    
    # Call the main chat handler
    chat_response = await handle_chat_query(chat_request)
    
    # Convert back to simple response format
    return QueryResponse(
        success=chat_response.success,
        query=chat_response.query,
        sql_query=chat_response.sql_query,
        data=chat_response.data,
        summary=chat_response.summary,
        insights=chat_response.insights,
        recommendation=chat_response.recommendation,
        response_summary=chat_response.response_summary,
        execution_time_ms=chat_response.execution_time_ms,
        record_count=chat_response.record_count
    )

@router.post("/sql-only", response_model=ApiResponse)
async def generate_sql_only(request: QueryRequest):
    """Generate SQL query without execution."""
    try:
        augmented_query = f"""
        User Query: {request.query}
        Available Dataset Columns: {json.dumps(TRANSACTION_COLUMNS, indent=2)}
        Please generate a PostgreSQL query to answer this question.
        """
        
        sql_result = await sql_agent.run(augmented_query)
        return ApiResponse(
            success=True,
            message="SQL query generated successfully",
            data=sql_result.data.dict()
        )
    except Exception as e:
        return ApiResponse(
            success=False,
            message="Failed to generate SQL",
            error=str(e)
        )

@router.get("/chats", response_model=ApiResponse)
async def get_all_chats():
    """Get all chat records from database as raw JSON objects."""
    try:
        raw_chats_data = await get_all_chats_from_db()
        
        # Convert records to JSON objects with proper timestamp serialization
        chat_records = []
        for record in raw_chats_data:
            chat_records.append({
                "id": record['id'],
                "chat_id": record['chat_id'],
                "query": record['query'],
                "timestamp": record['timestamp'].isoformat() if record['timestamp'] else None,
            })
        
        return ApiResponse(
            success=True,
            message=f"Retrieved {len(chat_records)} chat records",
            data={"chats": chat_records, "count": len(chat_records)}
        )
        
    except Exception as e:
        return ApiResponse(
            success=False,
            message="Failed to get chat records",
            error=str(e)
        )

@router.get("/chats/{chat_id}/history", response_model=ApiResponse)
async def get_chat_history_endpoint(chat_id: str):
    """Get message history for a specific chat from database."""
    try:
        db_history = await load_chat_history_from_db(chat_id)
        
        if not db_history:
            return ApiResponse(
                success=False,
                message=f"Chat {chat_id} not found",
                error="Chat not found"
            )
        
        # Get metadata from first and last messages
        first_msg = db_history[0] if db_history else None
        last_msg = db_history[-1] if db_history else None
        
        history = ChatHistory(
            chat_id=chat_id,
            messages=db_history,
            created_at=first_msg['timestamp'].isoformat() if first_msg else datetime.now().isoformat(),
            updated_at=last_msg['timestamp'].isoformat() if last_msg else datetime.now().isoformat()
        )
        
        return ApiResponse(
            success=True,
            message=f"Retrieved history for chat {chat_id}",
            data=history.dict()
        )
        
    except Exception as e:
        return ApiResponse(
            success=False,
            message=f"Failed to get chat history for {chat_id}",
            error=str(e)
        )

@router.delete("/chats/{chat_id}", response_model=ApiResponse)
async def delete_chat(chat_id: str):
    """Delete a specific chat conversation from database."""
    try:
        # Check if chat exists
        if not await chat_exists_in_db(chat_id):
            return ApiResponse(
                success=False,
                message=f"Chat {chat_id} not found",
                error="Chat not found"
            )
        
        # Delete from database
        success = await delete_chat_from_db(chat_id)
        
        if success:
            # Remove from memory cache if present
            delete_chat_from_memory(chat_id)
            
            return ApiResponse(
                success=True,
                message=f"Chat {chat_id} deleted successfully",
                data={"deleted_chat_id": chat_id}
            )
        else:
            return ApiResponse(
                success=False,
                message=f"Failed to delete chat {chat_id}",
                error="Database deletion failed"
            )
        
    except Exception as e:
        return ApiResponse(
            success=False,
            message=f"Failed to delete chat {chat_id}",
            error=str(e)
        )

@router.put("/chats/{chat_id}/title", response_model=ApiResponse)
async def update_chat_title(chat_id: str, title: str = Query(..., description="New title for the chat")):
    """Update the title of a chat conversation."""
    try:
        # For now, we'll store the title update as a special entry
        # In a more sophisticated implementation, you might add a separate title column
        # or store metadata separately
        
        if not await chat_exists_in_db(chat_id):
            return ApiResponse(
                success=False,
                message=f"Chat {chat_id} not found",
                error="Chat not found"
            )
        
        # Save the title update (you could modify this to update a separate title column)
        await save_chat_query(chat_id, f"[TITLE_UPDATE]: {title}", "title_update")
        
        return ApiResponse(
            success=True,
            message=f"Chat title updated successfully",
            data={
                "chat_id": chat_id,
                "new_title": title,
                "updated_at": datetime.now().isoformat()
            }
        )
        
    except Exception as e:
        return ApiResponse(
            success=False,
            message=f"Failed to update chat title for {chat_id}",
            error=str(e)
        )

@router.get("/chats/test", response_model=ApiResponse)
async def test_chat_persistence():
    """Test endpoint to verify chat persistence is working."""
    try:
        test_chat_id = f"test_chat_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        test_query = "Test query"
        
        # Test saving and loading
        await save_chat_query(test_chat_id, test_query, "test_response")
        history = await load_chat_history_from_db(test_chat_id)
        await delete_chat_from_db(test_chat_id)
        
        return ApiResponse(
            success=True,
            message="Chat persistence working",
            data={"records_found": len(history)}
        )
        
    except Exception as e:
        return ApiResponse(
            success=False,
            message="Chat persistence failed",
            error=str(e)
        ) 