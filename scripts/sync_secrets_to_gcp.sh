#!/bin/bash
set -e

# Usage: ./sync_secrets_to_gcp.sh <project_id>
PROJECT_ID=$1

if [ -z "$PROJECT_ID" ]; then
  echo "Error: Project ID is required."
  exit 1
fi

# List of secrets to sync
# The script expects these to be available as environment variables
SECRETS=(
  "GOOGLE_API_KEY"
  "WHATSAPP_API_TOKEN"
  "WHATSAPP_PHONE_NUMBER_ID"
  "WEBHOOK_VERIFY_TOKEN"
)

echo "Syncing secrets to GCP Project: $PROJECT_ID"

for SECRET_NAME in "${SECRETS[@]}"; do
  # Get the value from the environment variable
  SECRET_VALUE="${!SECRET_NAME}"

  if [ -z "$SECRET_VALUE" ]; then
    echo "Warning: Environment variable $SECRET_NAME is empty. Skipping."
    continue
  fi

  # Define the GCP Secret name (using a prefix to avoid collisions)
  # We use the same name for both environments (dev/prod) because they are in different projects.
  GCP_SECRET_NAME="luca-${SECRET_NAME//_/-}"

  echo "Processing $GCP_SECRET_NAME..."  # Check if secret exists
  if ! gcloud secrets describe "$GCP_SECRET_NAME" --project="$PROJECT_ID" &>/dev/null; then
    echo "Creating secret $GCP_SECRET_NAME..."
    gcloud secrets create "$GCP_SECRET_NAME" --replication-policy="automatic" --project="$PROJECT_ID"
  fi

  # Add a new version
  echo "Adding new version to $GCP_SECRET_NAME..."
  echo -n "$SECRET_VALUE" | gcloud secrets versions add "$GCP_SECRET_NAME" --data-file=- --project="$PROJECT_ID"
done

echo "Secrets sync complete."
