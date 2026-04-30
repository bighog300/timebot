#!/usr/bin/env bash
set -euo pipefail

if [ "${ALLOW_IMAGE_PUSH:-}" != "1" ]; then
  echo "Image push disabled. Set ALLOW_IMAGE_PUSH=1 only for intentional deploys."
  exit 1
fi

if [ $# -lt 1 ]; then
  echo "Usage: $0 <image[:tag]>"
  exit 1
fi

image="$1"
docker push "$image"
