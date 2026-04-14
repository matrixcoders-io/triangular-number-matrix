#!/bin/bash
# cloudrun/setup.sh
#
# One-time setup for Cloud Run deployment.
# Run this ONCE before your first deploy. Safe to re-run (all commands are idempotent).
#
# Usage (from project root):
#   bash cloudrun/setup.sh

set -euo pipefail

PROJECT="matrix-coders"
REGION="us-central1"
SA_NAME="tnm-cloudrun"
SA_EMAIL="${SA_NAME}@${PROJECT}.iam.gserviceaccount.com"
BUCKET="matrix-coders-tnm-output"
GAR_REPO="triangular-number-matrix"

echo "==> [1/5] Setting active project to ${PROJECT}"
gcloud config set project "${PROJECT}"

echo "==> [2/5] Creating GAR Docker repository (skipped if already exists)"
gcloud artifacts repositories describe "${GAR_REPO}" \
  --location="${REGION}" --project="${PROJECT}" 2>/dev/null \
|| gcloud artifacts repositories create "${GAR_REPO}" \
  --repository-format=docker \
  --location="${REGION}" \
  --project="${PROJECT}" \
  --description="Triangular Number Matrix app images"

echo "==> [3/5] Creating GCS bucket gs://${BUCKET} (skipped if already exists)"
gcloud storage buckets describe "gs://${BUCKET}" 2>/dev/null \
|| gcloud storage buckets create "gs://${BUCKET}" \
  --project="${PROJECT}" \
  --location="${REGION}" \
  --uniform-bucket-level-access

echo "==> [4/5] Creating service account ${SA_EMAIL} (skipped if already exists)"
gcloud iam service-accounts describe "${SA_EMAIL}" --project="${PROJECT}" 2>/dev/null \
|| gcloud iam service-accounts create "${SA_NAME}" \
  --project="${PROJECT}" \
  --display-name="Triangular Number Matrix — Cloud Run runtime"

echo "==> [4b/5] Granting service account read/write on GCS bucket"
gcloud storage buckets add-iam-policy-binding "gs://${BUCKET}" \
  --member="serviceAccount:${SA_EMAIL}" \
  --role="roles/storage.objectAdmin"

echo "==> [4c/5] Granting service account permission to use Cloud Run"
gcloud projects add-iam-policy-binding "${PROJECT}" \
  --member="serviceAccount:${SA_EMAIL}" \
  --role="roles/run.invoker"

echo "==> [5/5] Enabling required GCP APIs (safe to re-run)"
gcloud services enable \
  run.googleapis.com \
  artifactregistry.googleapis.com \
  storage.googleapis.com \
  --project="${PROJECT}"

echo ""
echo "✓ Setup complete."
echo ""
echo "Next step — map your custom domain (run once, after first deploy):"
echo "  gcloud beta run domain-mappings create \\"
echo "    --service=triangular-number-matrix \\"
echo "    --domain=tnm-calculator.matrixcoders.io \\"
echo "    --region=${REGION} \\"
echo "    --project=${PROJECT}"
echo ""
echo "Then point DNS CNAME for calculator.matrixcoders.io to the value shown above."
