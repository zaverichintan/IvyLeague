import json
from datetime import datetime
import os
import requests # Used for making HTTP requests to the Gemini API
import psycopg2
import pandas as pd 
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
load_dotenv()
import os


def fetch_transaction_events(db_config, transaction_id: str) -> list:
    """
    Fetches transaction event data from the database.
    
    Args:
        transaction_id: The unique identifier for the transaction.

    Returns:
        A list of event dictionaries for the given transaction, or an empty list if not found.
    """
        
    print(f"🔍 Searching for transaction: {transaction_id}")
        
    if isinstance(db_config, dict):
        connection_string = f"postgresql://{db_config['user']}:{db_config['password']}@{db_config['host']}:{db_config['port']}/{db_config['database']}"
    else:
        connection_string = db_config  # Assume it's already a connection string

        # Create engine
    engine = create_engine(connection_string)

        # SQL query to fetch transaction events
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
                onchain_fiat_transaction_data oftd
            where
                transaction_id = '{transaction_id}'
            """
    event_types_df = pd.DataFrame(engine.connect().execute(text(event_types_query))).to_dict('records')
 
    # In a real application, you would replace this with a database call.
    return event_types_df

def generate_summary_with_gemini(events: list) -> str:
    """
    Uses the Gemini API to generate a detailed failure analysis and mitigation plan.

    Args:
        events: A list of event dictionaries for the transaction.

    Returns:
        A string containing the AI-generated analysis.
    """
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        return "Error: GEMINI_API_KEY environment variable not set. Please set it to your Gemini API key."

    # The API endpoint for the gemini-2.5-flash model
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"

    # Construct a detailed prompt for the model
    prompt = f"""
    You are a senior ops engineer at a leading crypto transaction manager company. 
    Your task is to provide a detailed failure analysis for a crypto transaction based on the provided event log.
    error_message describes the source of the errorand the alert_description describes the description of alert sent to the user
    The analysis must be clear, concise, and actionable for technical stakeholders.
    Output the Diagnose root causes in 2 to 3 points, and generate a clear step-by-step remediation plan for ops teams in only 2 to 3 points.
    Here is the JSON event log for the transaction:
    {json.dumps(events, indent=2)}
    """

    # Prepare the payload for the API request
    payload = {
        "contents": [{
            "parts": [{
                "text": prompt
            }]
        }]
    }

    headers = {
        'Content-Type': 'application/json'
    }

    try:
        print("🤖 Calling Gemini API for analysis...")
        response = requests.post(url, headers=headers, data=json.dumps(payload))
        response.raise_for_status()  # Raise an exception for bad status codes (4xx or 5xx)
        
        response_json = response.json()
        
        # Extract the generated text from the API response
        if (response_json.get('candidates') and 
            response_json['candidates'][0].get('content') and 
            response_json['candidates'][0]['content'].get('parts')):
            
            return response_json['candidates'][0]['content']['parts'][0]['text']
        else:
            return f"Error: Received an unexpected response format from Gemini API.\n\n{response.text}"

    except requests.exceptions.RequestException as e:
        return f"Error calling Gemini API: {e}"
    except Exception as e:
        return f"An unexpected error occurred: {e}"

def analyze_and_summarize_failure_webhook(transaction_id: str):
    db_config = create_db_config_from_env()
    return analyze_and_summarize_failure(db_config, transaction_id)
    
def analyze_and_summarize_failure(db_config, transaction_id: str) -> str:
    """
    Analyzes a transaction's events to determine the cause of failure and generates a summary using the Gemini API.

    Args:
        transaction_id: The transaction to analyze.

    Returns:
        A string containing a detailed summary of the transaction failure.
    """

    events = fetch_transaction_events(db_config, transaction_id)
    
    if not events:
        return f"Transaction ID '{transaction_id}' not found."

    # Check for the final status of the transaction
    final_status_event = next((event for event in reversed(events) if event['event_type'] in ['PaymentRefunded', 'PaymentCompleted']), None)

    if final_status_event and final_status_event['event_type'] == 'PaymentCompleted':
        return f"Transaction '{transaction_id}' completed successfully."
        
    # Generate the summary using the Gemini API
    return generate_summary_with_gemini(events)

# Database connection examples and utility functions
def create_db_config_from_env():
    """Create database configuration from environment variables"""
    return {
        "host": os.getenv("DB_HOST", "localhost"),
        "port": os.getenv("DB_PORT", 5431),
        "database": os.getenv("DB_NAME", "postgres"),
        "user": os.getenv("DB_USER", "postgres"),
        "password": os.getenv("DB_PASSWORD", ""),
    }

# --- Example Usage ---
if __name__ == "__main__":
    # Use the example transaction ID from the mock database
    test_transaction_id = "0013dbb0-080a-4a69-8db5-f83131b149ac"
    db_config = create_db_config_from_env()

    # Generate the failure summary
    failure_summary = analyze_and_summarize_failure(db_config, 
                                                    test_transaction_id)
    
    # Print the report
    print("-" * 70)
    print(failure_summary)
    print("-" * 70)
# if __name__ == "__main__":
#     # Start the Flask web server.
#     # It will listen for incoming requests on all network interfaces on port 5001.
#     # To use this, you would configure Grafana's webhook to point to:
#     # http://<your_server_ip>:5001/webhook
#     print("\n🚀 Starting Flask server to listen for Grafana webhooks...")
#     print("👂 Listening on http://0.0.0.0:5001/webhook")
#     app.run(host='0.0.0.0', port=5001)