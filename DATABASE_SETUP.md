# 🗄️ Database Setup Guide

This guide explains how to set up the database persistence for chat conversations.

## 📋 Requirements

- PostgreSQL 10+ running and accessible
- Python environment with required packages installed
- Environment variables configured

## 🚀 Quick Setup

### 1. Environment Variables

Set up your environment variables:

```bash
# Main transactions database (required)
export DATABASE_URL="postgresql://username:password@localhost:5432/your_transactions_db"

# OpenAI API key (required)
export OPENAI_API_KEY="your_openai_api_key_here"

# Chat database (optional - will auto-derive)
export CHAT_DATABASE_URL="postgresql://username:password@localhost:5432/ivy"
```

### 2. Create Ivy Database

Run the helper script to create the `ivy` database:

```bash
python create_ivy_database.py
```

**What this does:**
- ✅ Checks if `ivy` database exists
- ✅ Creates it if it doesn't exist  
- ✅ Tests the connection
- ✅ Provides troubleshooting info

### 3. Start the API

```bash
uvicorn api:app --reload --port 8001
```

The API will automatically:
- ✅ Create connection pools for both databases
- ✅ Create the `chats` table with proper schema
- ✅ Add performance indexes
- ✅ Handle any initialization errors gracefully

## 🗃️ Database Schema

### Ivy Database Structure

**Database**: `ivy`  
**Table**: `chats`

```sql
CREATE TABLE chats (
    id SERIAL PRIMARY KEY,
    chat_id VARCHAR(255) NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    query TEXT,
    response TEXT
);

-- Indexes for performance
CREATE INDEX idx_chats_chat_id ON chats(chat_id);
CREATE INDEX idx_chats_timestamp ON chats(timestamp);
```

### Column Usage

- `id`: Auto-incrementing primary key
- `chat_id`: UUID for conversation grouping
- `timestamp`: When the query was made
- `query`: The user's natural language query
- `response`: Additional metadata (response type, etc.)

## 🔄 Dual Database Architecture

The system uses two separate databases:

### 1. Transactions Database
- **Purpose**: Your existing transaction data
- **Connection**: `DATABASE_URL`
- **Required**: Yes (API won't start without this)

### 2. Chat Database (ivy)
- **Purpose**: Conversation persistence
- **Connection**: `CHAT_DATABASE_URL` (auto-derived if not set)
- **Required**: No (API works without chat persistence)

## 🛡️ Error Handling

The system is designed to be resilient:

### Chat Database Unavailable
If the chat database fails to initialize:
- ✅ API still starts normally
- ✅ Transactions functionality works
- ✅ Conversations work (memory-only)
- ⚠️ Chat persistence is disabled
- ⚠️ Chat history is not saved

### Recovery
1. Fix the database issue
2. Restart the API
3. Chat persistence will resume

## 🔍 Health Check

Check system status:

```bash
curl http://localhost:8001/health
```

**Response includes:**
```json
{
  "success": true,
  "data": {
    "transactions_database": "connected",
    "chats_database": "connected",
    "transactions_pool_size": 10,
    "chats_pool_size": 5
  }
}
```

**Status Values:**
- `connected`: Database working normally
- `disabled`: Chat persistence disabled
- `error: ...`: Connection issues
- `not_initialized`: Pool not created

## 🐛 Troubleshooting

### Common Issues

1. **"Database ivy does not exist"**
   ```bash
   # Solution: Run the setup script
   python create_ivy_database.py
   ```

2. **"Permission denied to create database"**
   ```sql
   -- Solution: Grant permissions or create manually
   CREATE DATABASE ivy;
   GRANT ALL PRIVILEGES ON DATABASE ivy TO your_user;
   ```

3. **"Chat persistence will be disabled"**
   - Check PostgreSQL is running
   - Verify DATABASE_URL is correct
   - Ensure network connectivity

4. **Index creation errors**
   - The API handles this gracefully
   - Tables work without indexes (just slower)
   - Check PostgreSQL logs for details

### Manual Database Creation

If the script fails, create manually:

```sql
-- Connect to PostgreSQL as admin
psql -h localhost -U postgres

-- Create database
CREATE DATABASE ivy;

-- Create user (if needed)
CREATE USER api_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE ivy TO api_user;

-- Connect to ivy database
\c ivy

-- Tables will be created automatically by the API
```

### Logs and Debugging

Enable debug logging:

```bash
export LOG_LEVEL=DEBUG
uvicorn api:app --reload --port 8001
```

**Look for these log messages:**
- `Chats database connection pool initialized successfully`
- `Chats table 'chats' initialized successfully`
- `Chat persistence disabled - skipping save`

## 🔧 Configuration Options

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `DATABASE_URL` | Yes | None | Main transactions database |
| `CHAT_DATABASE_URL` | No | Auto-derived | Chat persistence database |
| `OPENAI_API_KEY` | Yes | None | OpenAI API access |

### Performance Tuning

Adjust connection pool sizes in `api.py`:

```python
# Transactions database pool
min_size=1, max_size=10

# Chats database pool  
min_size=1, max_size=5
```

## 📊 Monitoring

### Database Connections

Monitor pool usage via health endpoint:

```bash
# Check active connections
curl http://localhost:8001/health | jq '.data.transactions_active_connections'
curl http://localhost:8001/health | jq '.data.chats_active_connections'
```

### Chat Storage

Check stored conversations:

```sql
-- Connect to ivy database
SELECT chat_id, COUNT(*) as message_count, 
       MIN(timestamp) as first_message,
       MAX(timestamp) as last_message
FROM chats 
GROUP BY chat_id 
ORDER BY last_message DESC;
```

## 🔄 Migration

### From Memory-Only to Persistent

If upgrading from memory-only conversations:
1. Run database setup
2. Restart API
3. New conversations will be persistent
4. Old memory conversations are lost (expected)

### Backup Chat Data

```bash
# Export chat data
pg_dump -h localhost -U username -d ivy > ivy_backup.sql

# Restore chat data
psql -h localhost -U username -d ivy < ivy_backup.sql
```

This setup ensures robust chat persistence while maintaining system reliability! 