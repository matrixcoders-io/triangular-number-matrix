#!/bin/bash
# cloudrun/deploy.sh
#
# Build, push, and deploy in one command.
# Run from project root every time you want to ship a new version.
#
# Usage:
#   bash cloudrun/deploy.sh          # deploys :latest
#   bash cloudrun/deploy.sh v1.2.3   # deploys a specific tag

set -euo pipefail

PROJECT="matrix-coders"
REGION="us-central1"
IMAGE="us-central1-docker.pkg.dev/${PROJECT}/triangular-number-matrix/app"
TAG="${1:-latest}"
SERVICE_YAML="cloudrun/service.yaml"

echo "==> [1/4] Authorizing Docker to push to GAR"
gcloud auth configure-docker "${REGION}-docker.pkg.dev" --quiet

echo "==> [2/4] Building image ${IMAGE}:${TAG}"
# Build context is project root; Dockerfile lives in docker/
docker build \
  -f docker/Dockerfile \
  -t "${IMAGE}:${TAG}" \
  -t "${IMAGE}:latest" \
  .

echo "==> [3/4] Pushing image to GAR"
docker push "${IMAGE}:${TAG}"
# Also push :latest so service.yaml (pinned to :latest) always gets the new build
if [ "${TAG}" != "latest" ]; then
  docker push "${IMAGE}:latest"
fi

echo "==> [4/4] Deploying to Cloud Run (region: ${REGION})"
gcloud run services replace "${SERVICE_YAML}" \
  --region="${REGION}" \
  --project="${PROJECT}"

echo ""
echo "✓ Deployed. Service URL:"
gcloud run services describe triangular-number-matrix \
  --region="${REGION}" \
  --project="${PROJECT}" \
  --format="value(status.url)"
