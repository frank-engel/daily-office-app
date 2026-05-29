#!/usr/bin/env bash
# Toggle public access to the app without destroying infrastructure.
#
# Usage:
#   scripts/toggle-access.sh off   — take app offline (no inbound on ALB)
#   scripts/toggle-access.sh on    — bring app back online
#
# This re-runs terraform apply with the enable_public_access variable overridden.
# All other variables are read from terraform.tfvars as normal.
set -euo pipefail

INFRA_DIR="$(dirname "$0")/../infra"
cd "$INFRA_DIR"

usage() {
  echo "Usage: $0 [on|off]"
  echo "  on   — enable public access (bring app online)"
  echo "  off  — disable public access (take app offline, keep infrastructure)"
  exit 1
}

if [[ $# -ne 1 ]]; then
  usage
fi

case "$1" in
  on | true)
    echo "Enabling public access..."
    terraform init -input=false
    terraform apply -var="enable_public_access=true" -auto-approve
    echo "App is online."
    ;;
  off | false)
    echo "Disabling public access..."
    terraform init -input=false
    terraform apply -var="enable_public_access=false" -auto-approve
    echo "App is offline (infrastructure preserved)."
    ;;
  *)
    usage
    ;;
esac
