import uuid
import json
from typing import Dict, List, Any
from pydantic_ai.messages import ModelMessage
from ..database.connection import get_chats_db_connection
from ..config import CHAT_TABLE_NAME

# Keep minimal in-memory cache for PydanticAI message objects (not persistent)
chat_message_cache: Dict[str, List[ModelMessage]] = {}

def create_new_chat() -> str:
    """Create a new chat and return its ID."""
    chat_id = str(uuid.uuid4())
    chat_message_cache[chat_id] = []
    return chat_id

async def update_chat_history(chat_id: str, messages: List[ModelMessage], query: str = None, response_data: Any = None, response_summary: str = None):
    """Update chat history in memory cache and save query and response to database."""
    # Update in-memory cache for PydanticAI messages
    chat_message_cache[chat_id] = messages
    
    # Save query and response to database if provided
    if query:
        await save_chat_query(chat_id, query, response_data, response_summary)

def get_chat_history(chat_id: str) -> List[ModelMessage]:
    """Get chat history for a specific chat ID from memory cache."""
    return chat_message_cache.get(chat_id, [])

async def load_chat_messages_from_db(chat_id: str) -> List[ModelMessage]:
    """Load and reconstruct PydanticAI messages from database for conversation context.
    This is a simplified reconstruction - in practice you might want to store 
    the full message objects as JSON."""
    db_history = await load_chat_history_from_db(chat_id)
    
    # Get last 5 summaries for context
    conn = await get_chats_db_connection()
    summaries = await conn.fetch(f"""
        SELECT summary 
        FROM {CHAT_TABLE_NAME}
        WHERE chat_id = $1 AND summary IS NOT NULL
        ORDER BY timestamp DESC
        LIMIT 5
    """, chat_id)
    await conn.close()
    
    # Add summaries to message cache
    if chat_id not in chat_message_cache:
        chat_message_cache[chat_id] = []
        
    # Add summary context if available
    if summaries:
        summary_context = "\n".join([row['summary'] for row in summaries if row['summary']])
        if summary_context:
            from pydantic_ai.messages import ModelRequest, UserPromptPart
            context_msg = ModelRequest(parts=[UserPromptPart(content=f"Previous conversation context:\n{summary_context}")])
            chat_message_cache[chat_id].append(context_msg)
    
    return chat_message_cache.get(chat_id, [])

# --- Chat Database Persistence Functions ---

async def save_chat_query(chat_id: str, query: str, response_data: str = None, response_summary: str = None):
    """Save a chat query to the database."""
    try:
        conn = await get_chats_db_connection()
        
        # Convert response data to string if needed
        response_str = json.dumps(response_data, default=str) if response_data else None
        
        # Create table if it doesn't exist
        await conn.execute(f"""
        CREATE TABLE IF NOT EXISTS {CHAT_TABLE_NAME} (
            id SERIAL PRIMARY KEY,
            chat_id VARCHAR(255) NOT NULL,
            timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            query TEXT,
            response TEXT,
            summary TEXT
        )
        """)
        
        # Insert the record
        await conn.execute(f"""
        INSERT INTO {CHAT_TABLE_NAME} (chat_id, query, response, summary)
        VALUES ($1, $2, $3, $4)
        """, chat_id, query, response_str, response_summary)
        
        await conn.close()
            
    except Exception:
        pass  # Fail silently for POC

async def load_chat_history_from_db(chat_id: str) -> List[Dict[str, Any]]:
    """Load chat history from the database."""
    try:
        conn = await get_chats_db_connection()
        rows = await conn.fetch(f"""
        SELECT id, chat_id, timestamp, query, response, summary
        FROM {CHAT_TABLE_NAME}
        WHERE chat_id = $1
        ORDER BY timestamp ASC
        """, chat_id)
        await conn.close()
        return [dict(row) for row in rows]
    except Exception:
        return []

async def get_all_chats_from_db() -> List[Dict[str, Any]]:
    """Get all chat records from the database as they are stored."""
    try:
        conn = await get_chats_db_connection()
        rows = await conn.fetch(f"""
        SELECT DISTINCT ON (chat_id) id, chat_id, query, timestamp  
        FROM {CHAT_TABLE_NAME}
        ORDER BY chat_id, timestamp ASC
        """)
        await conn.close()
        return [dict(row) for row in rows]
    except Exception:
        return []

async def delete_chat_from_db(chat_id: str) -> bool:
    """Delete a chat from the database."""
    try:
        conn = await get_chats_db_connection()
        await conn.execute(f"DELETE FROM {CHAT_TABLE_NAME} WHERE chat_id = $1", chat_id)
        await conn.close()
        return True
    except Exception:
        return False

async def chat_exists_in_db(chat_id: str) -> bool:
    """Check if a chat exists in the database."""
    try:
        conn = await get_chats_db_connection()
        count = await conn.fetchval(f"SELECT COUNT(*) FROM {CHAT_TABLE_NAME} WHERE chat_id = $1", chat_id)
        await conn.close()
        return count > 0
    except Exception:
        return False

def delete_chat_from_memory(chat_id: str):
    """Remove chat from memory cache."""
    if chat_id in chat_message_cache:
        del chat_message_cache[chat_id] 


async def transaction_details_from_db(transaction_id: str) -> Dict[str, Any]:
    """Get transaction details from the database."""
    try:
        conn = await get_chats_db_connection()
        event_types_query = f"""    
            select
                affected_service,
                alert_description,
                event_index,
                event_type,
                provider,
                from_network,
                to_network,
                error_message,
                "timestamp" 
            from
                transactions oftd
            where
                transaction_id = '{transaction_id}'
        """
        rows = await conn.fetch(event_types_query)
        await conn.close()
        return [dict(row) for row in rows]
    except Exception:
        return {}
    
async def insert_transaction_details_to_db(transaction_id: str, details: Dict[str, Any]):
    """Insert transaction details into the database."""
    try:
        conn = await get_chats_db_connection()
        query = f"""    
        INSERT INTO alerts (transaction_id, summary) VALUES ($1, $2)
        """
        await conn.execute(query, transaction_id, details)
        await conn.close()
    except Exception as e:
        print(f"Error inserting transaction details into the database: {e}")
        pass
