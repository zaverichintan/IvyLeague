from flask import Flask, request, jsonify 
from ai_agent import analyze_and_summarize_failure_webhook
import json

app = Flask(__name__)

# @app.route('/webhook', methods=['GET'])

# --- Webhook Endpoint ---
@app.route('/webhook', methods=['POST'])
def grafana_webhook():
    """
    This endpoint listens for POST requests from Grafana's webhook notifier.
    It expects the transaction_id to be passed in the alert's tags.
    
    Example Grafana tag: transaction_id:txn_a7b3c9d1
    """
    try:
        data = request.json
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
        summary = analyze_and_summarize_failure_webhook(transaction_id)
        
        # In a real system, you would send this summary to Slack, PagerDuty, etc.
        # For this example, we just print it to the console.
        print("\n--- 📊 Grafana-Triggered Analysis Report 📊 ---")
        print(summary)
        print("-------------------------------------------------")

        return jsonify({"status": "success", "message": "Alert processed and analyzed."}), 200

    except Exception as e:
        print(f"An error occurred in the webhook: {e}")
        return jsonify({"status": "error", "message": "Internal server error"}), 500
    
if __name__ == "__main__":

    print("\n🚀 Starting Flask server to listen for Grafana webhooks...")
    print("👂 Listening on http://0.0.0.0:5001/webhook")
    app.run(host='0.0.0.0', port=5001)