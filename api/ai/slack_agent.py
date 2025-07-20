# 5ff0b83da77fd8dc702747555160acbf70e7a831d625cf73eb840b65f12f0fe9

import json
from dotenv import load_dotenv
from openai import OpenAI
from aci import ACI
load_dotenv()

openai = OpenAI()
aci = ACI()



def send_alert_to_slack(transaction_id: str, summary: str) -> None:
    # For a list of all supported apps and functions, please go to the platform.aci.dev
    print("Getting function definition for SLACK__CHAT_POST_MESSAGE")
    slack_send_message_function = aci.functions.get_definition("SLACK__CHAT_POST_MESSAGE")

    print("Sending request to OpenAI")
    response = openai.chat.completions.create(
        model="gpt-4o-2024-08-06",
        messages=[
            {
                "role": "system",
                "content": "You are a helpful assistant with access to a variety of tools.",
            },
            {
                "role": "user",
                "content": f"Send a message to our channel saying 'There is a new alert for transaction {transaction_id}. The summary is: {summary}'",
            },
        ],
        tools=[slack_send_message_function],

        tool_choice="required",  # force the model to generate a tool call for demo purposes
    )
    tool_call = (
        response.choices[0].message.tool_calls[0]
        if response.choices[0].message.tool_calls
        else None
    )

    if tool_call:
        print("Handling function call")
        result = aci.handle_function_call(
            tool_call.function.name,
            json.loads(tool_call.function.arguments),
            linked_account_owner_id="chintan"  # Replace with your actual linked account owner ID
        )

    return {"status": "success", "message": result}
 


def send_alert_via_email(recipient: str, transaction_id: str, summary: str) -> None:
    # Get function definition for Gmail send message
    gmail_send_message_function = aci.functions.get_definition("GMAIL__SEND_EMAIL")

    response = openai.chat.completions.create(
        model="gpt-4o-2024-08-06", 
        messages=[
            {
                "role": "system",
                "content": "You are a helpful assistant with access to a variety of tools.",
            },
            {
                "role": "user",
                "content": f"Send an email from 'zaverichintan5@gmail.com' to {recipient} with subject 'Transaction Alert: {transaction_id}' and body containing the summary: {summary}",
            },
        ],
        tools=[gmail_send_message_function],
        tool_choice="required",
    )

    tool_call = (
        response.choices[0].message.tool_calls[0]
        if response.choices[0].message.tool_calls
        else None
    )

    if tool_call:
        result = aci.handle_function_call(
            tool_call.function.name,
            json.loads(tool_call.function.arguments),
            linked_account_owner_id="chintan"  # Replace with your actual linked account owner ID
        )

    return {"status": "success", "message": result}