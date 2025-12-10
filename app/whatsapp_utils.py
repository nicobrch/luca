import os
import logging
import requests

# Setup logging
logger = logging.getLogger(__name__)


def get_whatsapp_credentials():
    token = os.getenv("WHATSAPP_API_TOKEN")
    phone_number_id = os.getenv("WHATSAPP_PHONE_NUMBER_ID")
    return token, phone_number_id


def send_whatsapp_message(to_number: str, message_body: str):
    token, phone_number_id = get_whatsapp_credentials()

    if not token or not phone_number_id:
        logger.error(
            "WhatsApp credentials not found (WHATSAPP_API_TOKEN or WHATSAPP_PHONE_NUMBER_ID)"
        )
        return None

    # API Version can be updated as needed
    url = f"https://graph.facebook.com/v21.0/{phone_number_id}/messages"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    data = {
        "messaging_product": "whatsapp",
        "to": to_number,
        "type": "text",
        "text": {"body": message_body},
    }

    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Error sending message: {e}")
        if e.response:
            logger.error(f"Response content: {e.response.text}")
        return None


def process_whatsapp_message(body):
    """
    Extracts the message and sender from the webhook body.
    """
    try:
        entry = body["entry"][0]
        changes = entry["changes"][0]
        value = changes["value"]

        if "messages" in value:
            message = value["messages"][0]
            sender_id = message["from"]

            message_text = ""
            message_type = message["type"]

            if message_type == "text":
                message_text = message["text"]["body"]
            elif message_type == "audio":
                # Handle audio if needed
                pass

            return {
                "sender_id": sender_id,
                "text": message_text,
                "type": message_type,
                "raw": message,
            }
        return None
    except (KeyError, IndexError) as e:
        logger.error(f"Error processing webhook body: {e}")
        return None
