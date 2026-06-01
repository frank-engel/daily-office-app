#!/usr/bin/env bash
# Toggle public access to the app without destroying infrastructure.
# Sets cloudfront_enabled=true/false on the CloudFront distribution.
# The distribution reports 503 to all clients within ~15 seconds of going offline.
#
# Usage:
#   scripts/toggle-access.sh off   — take app offline
#   scripts/toggle-access.sh on    — bring app back online
set -euo pipefail

INFRA_DIR="$(dirname "$0")/../infra"
cd "$INFRA_DIR"

usage() {
  echo "Usage: $0 [on|off]"
  echo "  on   — enable public access (CloudFront distribution enabled)"
  echo "  off  — disable public access (CloudFront returns 503, infrastructure preserved)"
  exit 1
}

if [[ $# -ne 1 ]]; then
  usage
fi

case "$1" in
  on | true)
    echo "Enabling public access..."
    terraform init -input=false
    terraform apply -var="cloudfront_enabled=true" -auto-approve
    echo "App is online."
    ;;
  off | false)
    echo "Disabling public access..."
    terraform init -input=false
    terraform apply -var="cloudfront_enabled=false" -auto-approve
    echo "App is offline (infrastructure preserved)."
    ;;
  *)
    usage
    ;;
esac
