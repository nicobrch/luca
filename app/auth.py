import logging
import os
from google.cloud import firestore

logger = logging.getLogger(__name__)

# Initialize Firestore client
# The client will automatically look for credentials in the environment
# (e.g. GOOGLE_APPLICATION_CREDENTIALS or metadata server on Cloud Run)
try:
    # Project ID is usually inferred, but can be set explicitly if needed
    project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
    if project_id:
        db = firestore.Client(project=project_id)
    else:
        db = firestore.Client()
except Exception as e:
    logger.warning(f"Could not initialize Firestore client: {e}")
    db = None


def get_user(user_id: str):
    """
    Retrieves a user document from Firestore by user_id (phone number).
    """
    if not db:
        logger.error("Firestore client is not initialized.")
        return None

    try:
        user_ref = db.collection("users").document(user_id)
        doc = user_ref.get()
        if doc.exists:
            return doc.to_dict()
        return None
    except Exception as e:
        logger.error(f"Error fetching user {user_id}: {e}")
        return None


def create_user(user_id: str, user_data: dict):
    """
    Creates or updates a user document in Firestore.
    """
    if not db:
        logger.error("Firestore client is not initialized.")
        return False

    try:
        # merge=True allows updating existing fields without overwriting the whole document
        db.collection("users").document(user_id).set(user_data, merge=True)
        return True
    except Exception as e:
        logger.error(f"Error creating/updating user {user_id}: {e}")
        return False
