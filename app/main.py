import os
import logging
from google.cloud import firestore
from fastapi import FastAPI, Request, HTTPException, Response
from .whatsapp_utils import process_whatsapp_message, send_whatsapp_message
from .auth import get_user, create_user

# Initialize FastAPI app
app = FastAPI(title="LUCA Webhook")

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@app.get("/")
async def health_check():
    return {"status": "ok", "service": "LUCA Webhook"}


@app.get("/webhook")
async def verify_webhook(request: Request):
    """
    Webhook verification for WhatsApp.
    """
    verify_token = os.getenv("WEBHOOK_VERIFY_TOKEN")
    mode = request.query_params.get("hub.mode")
    token = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge")

    if mode and token:
        if mode == "subscribe" and token == verify_token:
            logger.info("Webhook verified successfully.")
            return Response(content=challenge, media_type="text/plain")
        else:
            logger.warning("Webhook verification failed. Token mismatch.")
            raise HTTPException(status_code=403, detail="Verification failed")
    else:
        raise HTTPException(status_code=400, detail="Missing parameters")


@app.post("/webhook")
async def webhook_handler(request: Request):
    """
    Handle incoming messages from WhatsApp.
    """
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON")

    # Log the incoming webhook for debugging (be careful with PII in production)
    # logger.info(f"Received webhook: {body}")

    # Check if it's a status update or a message
    try:
        entry = body.get("entry", [])[0]
        changes = entry.get("changes", [])[0]
        value = changes.get("value", {})

        if "messages" not in value:
            # Likely a status update (sent, delivered, read)
            # You can handle status updates here if needed
            return {"status": "ignored_status_update"}

    except (IndexError, KeyError):
        return {"status": "ignored_malformed"}

    message_data = process_whatsapp_message(body)

    if message_data:
        sender_id = message_data["sender_id"]
        text = message_data["text"]

        logger.info(f"Message from {sender_id}: {text}")

        # Auth / User check
        user = get_user(sender_id)

        if not user:
            # Onboarding flow
            logger.info(f"New user {sender_id}. Starting onboarding.")
            # Initialize user profile
            create_user(
                sender_id,
                {"status": "onboarding", "created_at": firestore.SERVER_TIMESTAMP},
            )
            send_whatsapp_message(
                sender_id, "¡Hola! Soy LUCA, tu asistente financiero. ¿Cómo te llamas?"
            )
        else:
            # Existing user logic
            logger.info(f"User {sender_id} found. Processing message.")

            # TODO: Integrate with Agent Orchestrator here
            # For now, just echo or acknowledge
            # response = agent.process(text, user_context=user)

            send_whatsapp_message(sender_id, f"Recibido: {text}")

    return {"status": "processed"}
