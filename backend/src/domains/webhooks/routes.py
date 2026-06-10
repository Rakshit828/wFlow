from fastapi import APIRouter
from src.integrations.services.Google.api_client import GoogleAPIClient
from fastapi import status, Request
import base64
import json

webhooks_router = APIRouter()


@webhooks_router.post("/gmail", status_code=status.HTTP_200_OK)
async def gmail_webhook(request: Request):
    """
    Google Pub/Sub hits this endpoint IMMEDIATELY when an email arrives.
    """
    body = await request.json()
    
    # 1. Parse the incoming Pub/Sub message structure
    try:
        pubsub_message = body["message"]
        # Google encodes the actual internal notification payload in base64
        data_bytes = base64.b64decode(pubsub_message["data"])
        gmail_event = json.loads(data_bytes.decode("utf-8"))
        
        email_address = gmail_event.get("emailAddress")
        history_id = gmail_event.get("historyId")
        
        print(f"Notification received for: {email_address} (History ID: {history_id})")

    except (KeyError, ValueError) as e:
        print(f"Error ocurred: {e}")
        # Return 200/204 anyway so Google doesn't keep retrying bad payloads
        return {"status": "ignored", "reason": "invalid payload structure"}


    # # 2. Fetch the latest changes from Gmail using historyId
    # async with httpx.AsyncClient() as client:
    #     headers = {"Authorization": f"Bearer {ACCESS_TOKEN}"}
        
    #     # We list changes since this specific historyId to find the exact Message ID
    #     history_url = f"{GMAIL_API_BASE}/users/me/history?startHistoryId={history_id}"
    #     history_resp = await client.get(history_url, headers=headers)
        
    #     if history_resp.status_code != 200:
    #         print(f"Failed to fetch history: {history_resp.text}")
    #         return {"status": "failed_history_fetch"}
            
    #     history_data = history_resp.json()
        
    #     # Extract the message ID from the history records
    #     message_id = None
    #     if "history" in history_data:
    #         # Grab the latest message added
    #         for record in history_data["history"]:
    #             if "messagesAdded" in record:
    #                 message_id = record["messagesAdded"][0]["message"]["id"]
    #                 break

    #     if not message_id:
    #         return {"status": "no new messages found in this history batch"}

    #     # 3. Fetch the actual Email Body using the discovered message_id
    #     message_url = f"{GMAIL_API_BASE}/users/me/messages/{message_id}"
    #     message_resp = await client.get(message_url, headers=headers)
        
    #     if message_resp.status_code == 200:
    #         email_data = message_resp.json()
            
    #         # --- TRIGGER YOUR AI AGENT WORKFLOW HERE ---
    #         await trigger_ai_agent_worker(email_data)
            
    #     return {"status": "success"}

