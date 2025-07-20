import asyncpg
import logging
from fastapi import HTTPException
from ..config import DATABASE_URL, CHAT_DATABASE_URL, CHAT_DB_NAME

# Set up logger
logger = logging.getLogger(__name__)

# Constants
DATABASE_TIMEOUT = 60
CHAT_TABLE_NAME = "chats"

async def init_chats_table():
    """Initialize the chats table in the ivy database."""
    try:
        conn = await get_chats_db_connection()
        try:
            # Check if table exists and has correct structure
            table_exists = await conn.fetchval("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = $1
                )
            """, CHAT_TABLE_NAME)
            
            if table_exists:
                # Check if table has correct structure
                columns = await conn.fetch("""
                    SELECT column_name, data_type, column_default, is_nullable
                    FROM information_schema.columns
                    WHERE table_name = $1
                    ORDER BY ordinal_position
                """, CHAT_TABLE_NAME)
                
                # Check if timestamp column has proper default
                timestamp_ok = False
                for col in columns:
                    if col['column_name'] == 'timestamp' and col['column_default'] and 'CURRENT_TIMESTAMP' in str(col['column_default']):
                        timestamp_ok = True
                        break
                
                if not timestamp_ok:
                    logger.warning("Table exists but timestamp column doesn't have proper DEFAULT - recreating table")
                    await conn.execute(f"DROP TABLE IF EXISTS {CHAT_TABLE_NAME}")
                    table_exists = False
            
            if not table_exists:
                # Create the table with explicit column types and constraints
                create_table_sql = f"""
                CREATE TABLE {CHAT_TABLE_NAME} (
                    id SERIAL PRIMARY KEY,
                    chat_id VARCHAR(255) NOT NULL,
                    timestamp TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    query TEXT,
                    response TEXT,
                    summary TEXT
                )
                """
                await conn.execute(create_table_sql)
                logger.info(f"Created chats table '{CHAT_TABLE_NAME}' with proper schema")
            else:
                logger.info(f"Chats table '{CHAT_TABLE_NAME}' already exists with correct schema")
            
            # Create indexes separately with error handling
            try:
                await conn.execute(f"CREATE INDEX IF NOT EXISTS idx_{CHAT_TABLE_NAME}_chat_id ON {CHAT_TABLE_NAME}(chat_id)")
                logger.debug("Created chat_id index successfully")
            except Exception as e:
                logger.warning(f"Failed to create chat_id index (may already exist): {e}")
            
            try:
                await conn.execute(f"CREATE INDEX IF NOT EXISTS idx_{CHAT_TABLE_NAME}_timestamp ON {CHAT_TABLE_NAME}(timestamp)")
                logger.debug("Created timestamp index successfully")
            except Exception as e:
                logger.warning(f"Failed to create timestamp index (may already exist): {e}")
                
            # Test the table with a simple operation
            await test_chats_table(conn)
            
            logger.info(f"Chats table '{CHAT_TABLE_NAME}' initialization completed successfully")
        finally:
            await conn.close()
            
    except Exception as e:
        logger.error(f"Failed to initialize chats table: {e}")
        # Don't raise the error - the API can still work without chat persistence
        logger.warning("Chat persistence will be disabled due to table initialization failure")

async def test_chats_table(conn):
    """Test basic operations on the chats table."""
    try:
        test_chat_id = "test_chat_init"
        test_query = "test query"
        test_data = "test_data"
        
        # Test insert
        insert_sql = f"""
        INSERT INTO {CHAT_TABLE_NAME} (chat_id, query, response)
        VALUES ($1, $2, $3)
        """
        await conn.execute(insert_sql, test_chat_id, test_query, test_data)
        logger.debug("Test insert successful")
        
        # Test select
        select_sql = f"SELECT * FROM {CHAT_TABLE_NAME} WHERE chat_id = $1"
        result = await conn.fetch(select_sql, test_chat_id)
        if result:
            logger.debug("Test select successful")
        
        # Clean up test data
        delete_sql = f"DELETE FROM {CHAT_TABLE_NAME} WHERE chat_id = $1"
        await conn.execute(delete_sql, test_chat_id)
        logger.debug("Test cleanup successful")
        
    except Exception as e:
        logger.error(f"Chats table test failed: {e}")
        raise

async def get_transactions_db_connection():
    """Get a simple database connection for transactions."""
    transactions_db_url = DATABASE_URL
    if not transactions_db_url:
        raise RuntimeError("DATABASE_URL environment variable not set")
    
    try:
        return await asyncpg.connect(
            transactions_db_url,
            command_timeout=DATABASE_TIMEOUT,
            server_settings={
                'application_name': 'payment_ops_copilot_transactions',
            }
        )
    except Exception as e:
        logger.error(f"Failed to connect to transactions database: {e}")
        raise HTTPException(status_code=500, detail=f"Transactions database connection failed: {str(e)}")

async def get_chats_db_connection():
    """Get a simple database connection for chats."""
    chat_db_url = CHAT_DATABASE_URL
    if not chat_db_url:
        # If CHAT_DATABASE_URL not set, derive from transactions DB URL
        transactions_db_url = DATABASE_URL
        if transactions_db_url and "postgresql://" in transactions_db_url:
            # Replace database name with 'ivy'
            base_url = transactions_db_url.rsplit('/', 1)[0]
            chat_db_url = f"{base_url}/{CHAT_DB_NAME}"
        else:
            raise RuntimeError("Cannot derive chat database URL")
    
    try:
        return await asyncpg.connect(
            chat_db_url,
            command_timeout=DATABASE_TIMEOUT,
            server_settings={
                'application_name': 'payment_ops_copilot_chats',
            }
        )
    except Exception as e:
        logger.error(f"Failed to connect to chats database: {e}")
        raise HTTPException(status_code=500, detail=f"Chats database connection failed: {str(e)}")

# Backward compatibility function
async def get_db_connection():
    """Get database connection for transactions (backward compatibility)."""
    return await get_transactions_db_connection()

async def get_connection_status():
    """Get status of database connections."""
    try:
        # Test transactions database connection
        transactions_status = "unknown"
        try:
            conn = await get_transactions_db_connection()
            await conn.close()
            transactions_status = "available"
        except:
            transactions_status = "unavailable"
        
        # Test chats database connection
        chats_status = "unknown"
        try:
            conn = await get_chats_db_connection()
            await conn.close()
            chats_status = "available"
        except:
            chats_status = "unavailable"
        
        return {
            "transactions_database": transactions_status,
            "chats_database": chats_status,
            "connection_type": "simple_connections"
        }
    except Exception as e:
        logger.error(f"Error checking connection status: {e}")
        return {
            "transactions_database": "error",
            "chats_database": "error", 
            "connection_type": "simple_connections",
            "error": str(e)
        } 